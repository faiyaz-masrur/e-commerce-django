from rest_framework import serializers
from .models import Payment
from orders.models import Order


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'order', 'provider', 'transaction_id', 'status', 'raw_response',
                  'created_at', 'updated_at']
        read_only_fields = fields


class CreatePaymentIntentSerializer(serializers.Serializer):
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.filter(status='pending'),
        help_text="Order ID"
    )
    provider = serializers.ChoiceField(
        choices=['stripe', 'bkash'],
        help_text="Payment provider"
    )
    
    def validate(self, data):
        order_id = data.get('order_id')
        if Payment.objects.filter(order_id=order_id).exists():
            raise serializers.ValidationError(
                "A payment already exists for this order."
            )
        return data
