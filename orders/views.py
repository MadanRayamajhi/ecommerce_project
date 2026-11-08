from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction

from cart.models import Cart
from .models import Order, OrderItem


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)

    if not cart.items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('cart_detail')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not full_name or not address or not phone:
            messages.error(request, 'Please fill in all checkout fields.')
            return render(request, 'orders/checkout.html', {
                'cart': cart,
            })

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                full_name=full_name,
                address=address,
                phone=phone,
                total_price=cart.total_price,
            )

            for item in cart.items.select_related('product').all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity,
                )

            cart.items.all().delete()

        return redirect('order_success', order_id=order.id)

    return render(request, 'orders/checkout.html', {
        'cart': cart,
    })


@login_required
def order_success(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    return render(request, 'orders/order_success.html', {
        'order': order,
    })


@login_required
def order_list(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'orders/order_list.html', {
        'orders': orders,
    })