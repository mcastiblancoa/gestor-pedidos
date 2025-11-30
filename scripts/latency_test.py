import argparse
import json
import time
from statistics import median
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


def pctl(values, p):
    if not values:
        return 0
    values = sorted(values)
    k = (len(values) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return values[int(k)]
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return d0 + d1


def do_patch(session, url, order_id, status_value, headers=None, timeout=5.0):
    start = time.perf_counter()
    r = session.patch(f"{url}/orders/{order_id}/status/", json={"estado": status_value}, headers=headers or {}, timeout=timeout)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return (elapsed_ms, r.status_code, r.text[:200])


def main():
    parser = argparse.ArgumentParser(description='Latency test for PATCH /orders/{id}/status/')
    parser.add_argument('--base-url', default='http://localhost:8000', help='Base URL of the API')
    parser.add_argument('--order-id', required=True, help='Order ID (UUID) to update repeatedly')
    parser.add_argument('--runs', type=int, default=100, help='Number of total requests')
    parser.add_argument('--concurrency', type=int, default=1, help='Concurrent workers')
    parser.add_argument('--statuses', default='pendiente,en_proceso,enviado,entregado', help='Comma-separated statuses to cycle')
    parser.add_argument('--header', action='append', help='Extra header in Key:Value format. Can repeat.')
    args = parser.parse_args()

    headers = {}
    if args.header:
        for h in args.header:
            if ':' in h:
                k, v = h.split(':', 1)
                headers[k.strip()] = v.strip()

    statuses = [s.strip() for s in args.statuses.split(',') if s.strip()]
    latencies = []
    results = []

    with requests.Session() as session:
        if args.concurrency <= 1:
            for i in range(args.runs):
                s = statuses[i % len(statuses)]
                lat, code, body = do_patch(session, args.base_url, args.order_id, s, headers=headers)
                latencies.append(lat)
                results.append((code, body))
        else:
            with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
                futures = []
                for i in range(args.runs):
                    s = statuses[i % len(statuses)]
                    futures.append(ex.submit(do_patch, session, args.base_url, args.order_id, s, headers))
                for fut in as_completed(futures):
                    lat, code, body = fut.result()
                    latencies.append(lat)
                    results.append((code, body))

    med = median(latencies) if latencies else 0
    p95 = pctl(latencies, 95)
    p99 = pctl(latencies, 99)
    ok = med < 400
    print(json.dumps({
        'runs': args.runs,
        'concurrency': args.concurrency,
        'median_ms': round(med, 2),
        'p95_ms': round(p95, 2),
        'p99_ms': round(p99, 2),
        'meets_requirement_median_lt_400ms': ok,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
