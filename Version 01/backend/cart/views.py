from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)
from utils.responses import success_response, error_response


# ─── Helper: get or create the user's cart ────────────────────────────────────
def get_user_cart(user):
    """
    Returns the cart for this user.

    The Phase 3 signal auto-creates a cart when a user registers,
    so this should almost always just 'get'. The 'create' fallback
    handles edge cases like superusers created via createsuperuser
    before the signal was wired up.
    """
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 1: CartView
# GET /api/cart/
# ═════════════════════════════════════════════════════════════════════════════
class CartView(APIView):
    """
    Returns the full cart for the authenticated user.

    The response includes:
      - All cart items (product details + quantity + subtotal)
      - Cart totals (total_items, total_price, savings)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_user_cart(request.user)

        # prefetch_related: loads all cart items AND each item's product
        # in 2 additional queries instead of N queries (one per item)
        cart = Cart.objects.prefetch_related(
            'items__product__images',
            'items__product__category',
        ).get(pk=cart.pk)

        serializer = CartSerializer(cart, context={'request': request})
        return success_response(
            data=serializer.data,
            message="Cart retrieved successfully."
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 2: AddToCartView
# POST /api/cart/add/
# ═════════════════════════════════════════════════════════════════════════════
class AddToCartView(APIView):
    """
    Adds a product to the cart, or increases its quantity if already present.

    Request body:
        { "product_id": 5, "quantity": 2 }

    Logic:
        IF the product is already in the cart:
            new_qty = existing_qty + requested_qty
            IF new_qty > stock → reject with error
            ELSE → update quantity
        ELSE:
            create a new CartItem row

    We use transaction.atomic() to ensure the read-then-write is safe:
    if two requests arrive simultaneously, neither will corrupt the cart.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Could not add to cart.",
                errors=serializer.errors
            )

        product  = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        cart     = get_user_cart(request.user)

        with transaction.atomic():
            # Try to get an existing CartItem for this product
            cart_item = CartItem.objects.filter(cart=cart, product=product).first()

            if cart_item:
                # Product already in cart — check if combined quantity is valid
                new_quantity = cart_item.quantity + quantity
                if new_quantity > product.stock:
                    return error_response(
                        message=(
                            f"Cannot add {quantity} more. "
                            f"You already have {cart_item.quantity} in your cart and "
                            f"only {product.stock} are in stock."
                        ),
                        status_code=400
                    )
                cart_item.quantity = new_quantity
                cart_item.save()
                action = "updated"
            else:
                # New product — create a cart item row
                cart_item = CartItem.objects.create(
                    cart     = cart,
                    product  = product,
                    quantity = quantity
                )
                action = "added"

        # Return the full updated cart so the frontend can re-render
        updated_cart = Cart.objects.prefetch_related(
            'items__product__images',
            'items__product__category',
        ).get(pk=cart.pk)

        cart_serializer = CartSerializer(updated_cart, context={'request': request})

        return success_response(
            data={
                'cart':    cart_serializer.data,
                'message': f"'{product.name}' {action} to cart.",
            },
            message=f"'{product.name}' {action} to cart successfully.",
            status_code=200
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 3: CartItemView
# PATCH  /api/cart/items/<pk>/ → change quantity
# DELETE /api/cart/items/<pk>/ → remove this item
# ═════════════════════════════════════════════════════════════════════════════
class CartItemView(APIView):
    """
    Manages a single item already in the cart.

    PATCH: change the quantity of a specific cart item.
           Request body: { "quantity": 3 }
           Setting quantity to 0 is not allowed — use DELETE instead.

    DELETE: remove the item from the cart entirely.
    """
    permission_classes = [IsAuthenticated]

    def _get_cart_item(self, pk, user):
        """
        Gets a CartItem by pk, but ONLY if it belongs to the requesting user's cart.

        This is critical for security: without this check, user A could modify
        or delete items from user B's cart just by knowing the CartItem ID.
        """
        try:
            return CartItem.objects.select_related('product', 'cart').get(
                pk=pk,
                cart__user=user   # cart__user traverses FK: CartItem → Cart → User
            )
        except CartItem.DoesNotExist:
            return None

    def _return_updated_cart(self, cart, request):
        """Helper to return the full updated cart after any modification."""
        updated = Cart.objects.prefetch_related(
            'items__product__images',
            'items__product__category',
        ).get(pk=cart.pk)
        return CartSerializer(updated, context={'request': request}).data

    def patch(self, request, pk):
        """Update quantity of a cart item."""
        item = self._get_cart_item(pk, request.user)
        if not item:
            return error_response(
                message="Cart item not found.",
                status_code=404
            )

        # Pass the cart_item in context so the serializer can check stock
        serializer = UpdateCartItemSerializer(
            data=request.data,
            context={'cart_item': item}
        )
        if not serializer.is_valid():
            return error_response(
                message="Could not update quantity.",
                errors=serializer.errors
            )

        item.quantity = serializer.validated_data['quantity']
        item.save()

        return success_response(
            data=self._return_updated_cart(item.cart, request),
            message=f"Quantity updated to {item.quantity}."
        )

    def delete(self, request, pk):
        """Remove a single item from the cart."""
        item = self._get_cart_item(pk, request.user)
        if not item:
            return error_response(
                message="Cart item not found.",
                status_code=404
            )

        cart        = item.cart
        product_name = item.product.name
        item.delete()

        return success_response(
            data=self._return_updated_cart(cart, request),
            message=f"'{product_name}' removed from cart."
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 4: ClearCartView
# DELETE /api/cart/clear/
# ═════════════════════════════════════════════════════════════════════════════
class ClearCartView(APIView):
    """
    Removes ALL items from the user's cart.
    Used after a successful order is placed, or when the user manually clears.

    The Cart record itself is NOT deleted — only the CartItem rows are.
    This keeps the one-to-one relationship with User intact.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = get_user_cart(request.user)
        count = cart.items.count()
        cart.items.all().delete()   # Delete all CartItem rows for this cart

        return success_response(
            data={'total_items': 0, 'total_price': '0.00', 'items': []},
            message=f"Cart cleared. {count} item(s) removed."
        )
