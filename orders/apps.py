from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'orders'

    def ready(self):
        # Initialize MongoDB indexes at startup
        try:
            from .db import init_indexes
            init_indexes()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Mongo index init skipped: {e}")
