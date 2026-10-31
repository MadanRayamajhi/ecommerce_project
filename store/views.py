
from django.shortcuts import render
from .models import Product, Category


def home(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()

    context = {
        "products": products,
        "categories": categories,
    }

    return render(request, "store/home.html", context)
