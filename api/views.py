from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from store.models import Product, Category
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem

from .serializers import (
    ProductSerializer,
    CategorySerializer,
    CartSerializer,
    OrderSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    filterset_fields = ['category']
    search_fields = ['name']


class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        try:
            quantity = int(quantity)
            if quantity < 1:
                return Response(
                    {'error': 'Quantity must be at least 1.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (TypeError, ValueError):
            return Response(
                {'error': 'Invalid quantity.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = get_object_or_404(
            Product,
            id=product_id,
            is_active=True,
        )

        if product.stock < quantity:
            return Response(
                {'error': 'Insufficient stock.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart, _ = Cart.objects.get_or_create(user=request.user)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity},
        )

        if not created:
            if item.quantity + quantity > product.stock:
                return Response(
                    {'error': 'Insufficient stock.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            item.quantity += quantity
            item.save()

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        item = get_object_or_404(
            CartItem,
            cart=cart,
            id=pk,
        )
        item.delete()

        return Response(CartSerializer(cart).data)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    @transaction.atomic
    def perform_create(self, serializer):
        cart = Cart.objects.select_for_update().get(
            user=self.request.user
        )

        cart_items = list(cart.items.select_related('product').all())

        if not cart_items:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'error': 'Your cart is empty.'})

        for item in cart_items:
            if item.quantity > item.product.stock:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'error': f'Insufficient stock for {item.product.name}.'
                })

        order = serializer.save(
            user=self.request.user,
            total_price=cart.total_price,
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity,
            )

            item.product.stock -= item.quantity
            item.product.save(update_fields=['stock'])

        cart.items.all().delete()