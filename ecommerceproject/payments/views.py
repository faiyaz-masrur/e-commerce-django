
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins, generics

from accounts.permissions import IsAdmin
from .models import Payment
from orders.models import Order
from .serializers import (
    PaymentSerializer,
    CreatePaymentIntentSerializer,
)
from .stripe_service import StripePaymentService
import stripe

logger = logging.getLogger(__name__)


class PaymentViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    generics.GenericAPIView):
    
    queryset = Payment.objects.all()
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create_intent':
            return CreatePaymentIntentSerializer
        return PaymentSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Payment.objects.all()
        return Payment.objects.filter(order__user=user)
    
    def get(self, request, *args, **kwargs):
        if self.kwargs.get('pk'):
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data['order_id']
        provider = serializer.validated_data['provider']
        
        try:
            order = Order.objects.get(id=order_id, user=request.user, status='pending')
            
            if provider == 'stripe':

                payment_intent_data = StripePaymentService.create_payment_intent(order)

                payment = Payment.objects.create(
                    order=order,
                    provider='stripe',
                    transaction_id=payment_intent_data['payment_intent_id'],
                    status='pending',
                    raw_response=payment_intent_data,
                )
                
                logger.info(f"Payment intent created for order {order_id}")
                
                return Response({
                    'success': True,
                    'message': 'Payment intent created successfully',
                    'client_secret': payment_intent_data['client_secret'],
                    'payment_intent_id': payment_intent_data['payment_intent_id'],
                    'amount': payment_intent_data['amount'],
                    'currency': payment_intent_data['currency'],
                    'payment_id': payment.id,
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': f'Payment provider {provider} not yet implemented'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Order not found or not in pending status'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
