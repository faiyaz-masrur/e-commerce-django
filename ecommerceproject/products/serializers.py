from rest_framework import serializers
from .models import Category, Product, ProductCategory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']


class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'status']


class ProductSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'description', 'price', 'stock',
            'status', 'categories', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        categories = instance.categories.all()
        representation['categories'] = CategorySerializer(categories, many=True).data
        return representation
