from django.urls import path
from .views import CategoryListCreateDestroyAPIView, ProductListCreateAPIView

urlpatterns = [
    path('categories/', CategoryListCreateDestroyAPIView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryListCreateDestroyAPIView.as_view(), name='category-detail-delete'),
    path('', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('<int:pk>/', ProductListCreateAPIView.as_view(), name='product-detail-update-delete'),
]
