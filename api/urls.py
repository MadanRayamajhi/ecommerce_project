from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .views import (
    ProductViewSet,
    CategoryViewSet,
    CartViewSet,
    OrderViewSet,
)

router = DefaultRouter()
router.register('products', ProductViewSet, basename='api-product')
router.register('categories', CategoryViewSet, basename='api-category')
router.register('cart', CartViewSet, basename='api-cart')
router.register('orders', OrderViewSet, basename='api-order')

urlpatterns = [
    path('', include(router.urls)),
    path('token-auth/', obtain_auth_token, name='api_token_auth'),
]