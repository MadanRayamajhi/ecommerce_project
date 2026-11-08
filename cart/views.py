from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from store.models import Product
from .models import Cart, CartItem


@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    return render(request, 'cart/cart_detail.html', {
        'cart': cart,
    })


@login_required
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True,
    )

    cart, _ = Cart.objects.get_or_create(user=request.user)

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1},
    )

    if not created:
        item.quantity += 1
        item.save(update_fields=['quantity'])

    return redirect('cart_detail')


@login_required
@require_POST
def cart_remove(request, item_id):
    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user,
    )

    item.delete()

    return redirect('cart_detail')


@login_required
@require_POST
def cart_update(request, item_id):
    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user,
    )

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        return redirect('cart_detail')

    if quantity > 0:
        item.quantity = quantity
        item.save(update_fields=['quantity'])
    else:
        item.delete()

    return redirect('cart_detail')