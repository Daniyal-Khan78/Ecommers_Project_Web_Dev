from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import Wishlist
from .serializers import WishlistSerializer, AddToWishlistSerializer
from products.models import Product
from utils.responses import success_response, error_response


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 1: WishlistView
# GET /api/wishlist/
# ═════════════════════════════════════════════════════════════════════════════
class WishlistView(APIView):
    """
    Returns all products the authenticated user has saved to their wishlist.
    Results are ordered newest-first (most recently added at the top).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = Wishlist.objects.filter(
            user=request.user
        ).select_related(
            'product__category'
        ).prefetch_related(
            'product__images'
        ).order_by('-added_at')

        serializer = WishlistSerializer(
            items,
            many=True,
            context={'request': request}
        )
        return success_response(
            data=serializer.data,
            message=f"{items.count()} item(s) in your wishlist."
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 2: AddToWishlistView
# POST /api/wishlist/add/
# ═════════════════════════════════════════════════════════════════════════════
class AddToWishlistView(APIView):
    """
    Adds a product to the user's wishlist (the heart button).

    Idempotent: if the product is already wishlisted, returns success
    without creating a duplicate (the unique_together constraint on the
    Wishlist model prevents duplicates at the DB level too).

    Request body: { "product_id": 5 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToWishlistSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Could not add to wishlist.",
                errors=serializer.errors
            )

        product = serializer.product
        # get_or_create: atomically checks if the row exists.
        # created=True  → new row inserted
        # created=False → row already existed (idempotent success)
        wishlist_item, created = Wishlist.objects.get_or_create(
            user    = request.user,
            product = product
        )

        if created:
            message = f"'{product.name}' added to your wishlist."
        else:
            message = f"'{product.name}' is already in your wishlist."

        item_serializer = WishlistSerializer(
            wishlist_item,
            context={'request': request}
        )
        return success_response(
            data={
                'item':    item_serializer.data,
                'created': created,
            },
            message=message,
            status_code=201 if created else 200
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 3: RemoveFromWishlistView
# DELETE /api/wishlist/remove/<pk>/
# ═════════════════════════════════════════════════════════════════════════════
class RemoveFromWishlistView(APIView):
    """
    Removes a product from the user's wishlist (un-heart).

    Uses the wishlist entry's own pk (id), not the product_id.
    The frontend stores the wishlist item ID when it loads the wishlist,
    and sends it here when the user clicks the heart again.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            # Only allow deleting your OWN wishlist items
            item = Wishlist.objects.get(pk=pk, user=request.user)
        except Wishlist.DoesNotExist:
            return error_response(
                message="Wishlist item not found.",
                status_code=404
            )

        product_name = item.product.name
        item.delete()
        return success_response(
            message=f"'{product_name}' removed from your wishlist."
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 4: WishlistCheckView
# GET /api/wishlist/check/<product_id>/
# ═════════════════════════════════════════════════════════════════════════════
class WishlistCheckView(APIView):
    """
    Checks if a specific product is in the user's wishlist.

    Used by the React product card/detail component to determine
    whether to show a filled or empty heart icon.

    Returns: { "is_wishlisted": true/false, "wishlist_item_id": 42 or null }

    The wishlist_item_id is returned so the frontend can call
    DELETE /api/wishlist/remove/<wishlist_item_id>/ directly without
    needing to store or look up the ID separately.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        try:
            item = Wishlist.objects.get(user=request.user, product_id=product_id)
            return success_response(data={
                'is_wishlisted':   True,
                'wishlist_item_id': item.pk,
            })
        except Wishlist.DoesNotExist:
            return success_response(data={
                'is_wishlisted':   False,
                'wishlist_item_id': None,
            })


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 5: MoveToCartView
# POST /api/wishlist/<pk>/move-to-cart/
# ═════════════════════════════════════════════════════════════════════════════
class MoveToCartView(APIView):
    """
    Moves a wishlisted product directly into the cart.
    Convenience endpoint used by "Move to Cart" button on the wishlist page.

    Steps:
      1. Verify wishlist item belongs to this user
      2. Add the product to cart (quantity=1)
      3. Remove from wishlist
      4. Return updated wishlist
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            wishlist_item = Wishlist.objects.select_related('product').get(
                pk=pk,
                user=request.user
            )
        except Wishlist.DoesNotExist:
            return error_response(message="Wishlist item not found.", status_code=404)

        product = wishlist_item.product

        # Check product is still available
        if not product.is_available or product.stock == 0:
            return error_response(
                message=f"'{product.name}' is currently out of stock.",
                status_code=400
            )

        # Add to cart (import here to avoid circular imports)
        from cart.models import Cart, CartItem
        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )
        if not created:
            # Already in cart — increment by 1 if stock allows
            if cart_item.quantity + 1 <= product.stock:
                cart_item.quantity += 1
                cart_item.save()

        # Remove from wishlist
        wishlist_item.delete()

        # Return updated wishlist
        remaining = Wishlist.objects.filter(
            user=request.user
        ).select_related('product__category').prefetch_related('product__images')

        serializer = WishlistSerializer(
            remaining, many=True, context={'request': request}
        )
        return success_response(
            data=serializer.data,
            message=f"'{product.name}' moved to your cart."
        )
