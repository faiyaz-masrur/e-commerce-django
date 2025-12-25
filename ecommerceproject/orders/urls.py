from django.urls import path
from .views import OrderListCreateAPIView, OrderRetrieveUpdateAPIView

urlpatterns = [
    path('', OrderListCreateAPIView.as_view(), name='order-list-create'),
    path('<int:pk>/', OrderRetrieveUpdateAPIView.as_view(), name='order-detail'),
]
