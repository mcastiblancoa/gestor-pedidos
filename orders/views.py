import logging
import uuid
from typing import Any, Dict

from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample

from .db import get_orders_collection, now_utc
from .serializers import (
    OrderCreateSerializer,
    OrderUpdateSerializer,
    OrderStatusUpdateSerializer,
    OrderReadSerializer,
)

logger = logging.getLogger(__name__)


def _doc_to_order(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'id': d.get('_id'),
        'producto_id': d.get('producto_id'),
        'cantidad': d.get('cantidad'),
        'vendedor_id': d.get('vendedor_id'),
        'estado': d.get('estado'),
        'fecha_creacion': d.get('fecha_creacion'),
        'fecha_actualizacion': d.get('fecha_actualizacion'),
    }


def _get_or_404(order_id: str) -> Dict[str, Any]:
    col = get_orders_collection()
    doc = col.find_one({'_id': order_id})
    if not doc:
        raise Http404('Pedido no encontrado')
    return doc


@extend_schema(
    request=OrderCreateSerializer,
    responses={200: OrderReadSerializer},
    examples=[
        OpenApiExample(
            'Crear pedido',
            value={'producto_id': 'SKU-123', 'cantidad': 2, 'vendedor_id': 'S-01', 'estado': 'pendiente'},
            request_only=True,
        )
    ],
)
class OrderListCreateView(APIView):
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        page = max(page, 1)
        page_size = min(max(page_size, 1), 200)
        col = get_orders_collection()
        total = col.count_documents({})
        cursor = (
            col.find({}, projection={'_id': 1, 'producto_id': 1, 'cantidad': 1, 'vendedor_id': 1, 'estado': 1, 'fecha_creacion': 1, 'fecha_actualizacion': 1})
            .sort('fecha_creacion', -1)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        items = [_doc_to_order(d) for d in cursor]
        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': items,
        })

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        col = get_orders_collection()
        order_id = str(uuid.uuid4())
        now = now_utc()
        doc = {
            '_id': order_id,
            'producto_id': data['producto_id'],
            'cantidad': data['cantidad'],
            'vendedor_id': data['vendedor_id'],
            'estado': data['estado'],
            'fecha_creacion': now,
            'fecha_actualizacion': now,
        }
        col.insert_one(doc)
        return Response(_doc_to_order(doc), status=status.HTTP_201_CREATED)


@extend_schema(responses={200: OrderReadSerializer})
class OrderDetailView(APIView):
    def get(self, request, order_id: str):
        doc = _get_or_404(order_id)
        return Response(_doc_to_order(doc))

    @extend_schema(request=OrderUpdateSerializer, responses={200: OrderReadSerializer})
    def put(self, request, order_id: str):
        serializer = OrderUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        col = get_orders_collection()
        now = now_utc()
        update = {
            '$set': {
                'producto_id': data['producto_id'],
                'cantidad': data['cantidad'],
                'vendedor_id': data['vendedor_id'],
                'estado': data['estado'],
                'fecha_actualizacion': now,
            }
        }
        res = col.find_one_and_update({'_id': order_id}, update, return_document=True)
        if not res:
            raise Http404('Pedido no encontrado')
        # Keep original fecha_creacion if present
        if 'fecha_creacion' not in res:
            res['fecha_creacion'] = now
        return Response(_doc_to_order(res))

    def delete(self, request, order_id: str):
        col = get_orders_collection()
        res = col.delete_one({'_id': order_id})
        if res.deleted_count == 0:
            raise Http404('Pedido no encontrado')
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request=OrderStatusUpdateSerializer,
    responses={200: OrderReadSerializer},
    examples=[
        OpenApiExample('Actualizar estado', value={'estado': 'enviado'}, request_only=True),
    ],
)
class OrderStatusUpdateView(APIView):
    # Optimized for latency: minimal validation, single atomic update, minimal fields returned
    def patch(self, request, order_id: str):
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['estado']
        col = get_orders_collection()
        now = now_utc()
        updated = col.find_one_and_update(
            {'_id': order_id},
            {'$set': {'estado': new_status, 'fecha_actualizacion': now}},
            projection={'_id': 1, 'estado': 1, 'fecha_actualizacion': 1, 'producto_id': 1, 'cantidad': 1, 'vendedor_id': 1, 'fecha_creacion': 1},
            return_document=True,
        )
        if not updated:
            raise Http404('Pedido no encontrado')
        return Response(_doc_to_order(updated), status=status.HTTP_200_OK)
