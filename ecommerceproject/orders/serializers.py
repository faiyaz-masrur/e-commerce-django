from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.CharField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_name', 'quantity', 'price', 'subtotal']
        read_only_fields = ['id', 'quantity', 'price', 'subtotal']


class OrderCreateSerializer(serializers.Serializer):
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            allow_empty=False
        ),
        allow_empty=False
    )

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item.")
        
        for item in value:
            if 'product_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError(
                    "Each item must have 'product_id' and 'quantity'."
                )
            if item['quantity'] <= 0:
                raise serializers.ValidationError("Quantity must be greater than 0.")
            
            try:
                Product.objects.get(id=item['product_id'])
            except Product.DoesNotExist:
                raise serializers.ValidationError(
                    f"Product with id {item['product_id']} does not exist."
                )
        
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        items_data = validated_data['items']

        total_amount = self._calculate_total(items_data)
        
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            status='pending'
        )
        
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            quantity = item_data['quantity']
            
            subtotal = product.price * quantity
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price,
                subtotal=subtotal
            )
        
        return order

    def _calculate_total(self, items_data):
        total = 0
        for item in items_data:
            product = Product.objects.get(id=item['product_id'])
            subtotal = product.price * item['quantity']
            total += subtotal
        return total


class OrderSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source='user.id', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user_id', 'user_name', 'total_amount', 'status', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_amount', 'status', 'created_at', 'updated_at']


class OrderListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'user_name', 'total_amount', 'status', 'item_count', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

    def get_item_count(self, obj):
        return obj.items.count()


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']
        
    def validate_status(self, value):
        valid_statuses = ['pending', 'paid', 'cancelled']
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        return value

