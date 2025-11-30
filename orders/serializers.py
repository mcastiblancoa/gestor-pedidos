from datetime import datetime
from rest_framework import serializers
from .validators import ALLOWED_STATUSES


class OrderBaseSerializer(serializers.Serializer):
    producto_id = serializers.CharField(max_length=200)
    cantidad = serializers.IntegerField(min_value=1)
    vendedor_id = serializers.CharField(max_length=200)
    estado = serializers.ChoiceField(choices=sorted(list(ALLOWED_STATUSES)))


class OrderCreateSerializer(OrderBaseSerializer):
    pass


class OrderUpdateSerializer(OrderBaseSerializer):
    pass


class OrderStatusUpdateSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=sorted(list(ALLOWED_STATUSES)))


class OrderReadSerializer(serializers.Serializer):
    id = serializers.CharField()
    producto_id = serializers.CharField()
    cantidad = serializers.IntegerField()
    vendedor_id = serializers.CharField()
    estado = serializers.CharField()
    fecha_creacion = serializers.DateTimeField()
    fecha_actualizacion = serializers.DateTimeField()
