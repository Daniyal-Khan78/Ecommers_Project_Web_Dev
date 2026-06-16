from django.urls import path
from .views import CartView, AddToCartView, CartItemView, ClearCartView

# All URLs prefixed with /api/cart/ (set in backend/urls.py)
urlpatterns = [
    # View the full cart
    path('',           CartView.as_view(),      name='cart_view'),

    # Add a product to the cart (or increment quantity)
    path('add/',       AddToCartView.as_view(),  name='cart_add'),

    # Clear all items from the cart
    # IMPORTANT: 'clear/' must come BEFORE '<int:pk>/' so it is matched first
    path('clear/',     ClearCartView.as_view(),  name='cart_clear'),

    # Update quantity or remove a specific cart item
    path('items/<int:pk>/', CartItemView.as_view(), name='cart_item'),
]
