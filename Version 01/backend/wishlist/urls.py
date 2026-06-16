from django.urls import path
from .views import (
    WishlistView,
    AddToWishlistView,
    RemoveFromWishlistView,
    WishlistCheckView,
    MoveToCartView,
)

# All URLs prefixed with /api/wishlist/ (set in backend/urls.py)
urlpatterns = [
    # View full wishlist
    path('',                              WishlistView.as_view(),           name='wishlist_view'),

    # Add product to wishlist
    path('add/',                          AddToWishlistView.as_view(),      name='wishlist_add'),

    # Check if a product is wishlisted (for heart icon state)
    path('check/<int:product_id>/',       WishlistCheckView.as_view(),      name='wishlist_check'),

    # Remove a specific wishlist item by its own ID
    path('remove/<int:pk>/',              RemoveFromWishlistView.as_view(), name='wishlist_remove'),

    # Move wishlist item to cart
    path('<int:pk>/move-to-cart/',        MoveToCartView.as_view(),         name='wishlist_move_to_cart'),
]
