import os
import logging
from datetime import datetime, timezone
from typing import Optional

from pymongo import MongoClient, ASCENDING, ReturnDocument

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None


def _build_mongo_uri():
    host = os.environ.get('DB_HOST', 'localhost')
    port = int(os.environ.get('DB_PORT', '27017'))
    user = os.environ.get('DB_USER', '')
    pw = os.environ.get('DB_PASS', '')
    dbname = os.environ.get('DB_NAME', 'inventory_db')
    if user and pw:
        return f"mongodb://{user}:{pw}@{host}:{port}/{dbname}?authSource=admin"
    return f"mongodb://{host}:{port}/{dbname}"


def get_client() -> MongoClient:
    global _client
    if _client is None:
        uri = _build_mongo_uri()
        _client = MongoClient(uri, appname='inventory_manager')
    return _client


def get_db():
    dbname = os.environ.get('DB_NAME', 'inventory_db')
    return get_client()[dbname]


def get_orders_collection():
    return get_db()['orders']


def init_indexes():
    col = get_orders_collection()
    # _id index exists by default. Add useful secondary indexes for potential queries
    col.create_index([('vendedor_id', ASCENDING)])
    col.create_index([('estado', ASCENDING)])
    col.create_index([('fecha_creacion', ASCENDING)])
    logger.info('MongoDB indexes ensured for orders collection')


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
