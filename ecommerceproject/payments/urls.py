from django.urls import path
from .views import PaymentViewSet
from .webhook import stripe_webhook

app_name = 'payments'

urlpatterns = [
    # Payment endpoints
    path('', PaymentViewSet.as_view(), name='payment-list'),
    path('<int:pk>/', PaymentViewSet.as_view(), name='payment-detail'),
    
    # Webhook endpoint for Stripe
    path('webhook/stripe/', stripe_webhook, name='stripe_webhook'),
]
