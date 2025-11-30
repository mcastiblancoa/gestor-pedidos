from django.urls import path
from .views import OrderListCreateView, OrderDetailView, OrderStatusUpdateView

urlpatterns = [
    path('orders/', OrderListCreateView.as_view(), name='orders-list-create'),
    path('orders/<str:order_id>/', OrderDetailView.as_view(), name='orders-detail'),
    path('orders/<str:order_id>/status/', OrderStatusUpdateView.as_view(), name='orders-status'),
]
