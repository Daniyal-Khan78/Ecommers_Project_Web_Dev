from django.db import models
from django.conf import settings


# ─────────────────────────────────────────────────────────────
# MODEL 5: Cart
# ─────────────────────────────────────────────────────────────
class Cart(models.Model):
    """
    Represents a shopping cart. Every registered user gets exactly one cart.
    The cart persists between sessions (not lost when user closes browser).

    Relationship: User ←→ Cart is One-to-One.
    OneToOneField means each User has at most ONE Cart,
    and each Cart belongs to exactly ONE User.
    """

    # OneToOneField is like ForeignKey but enforces uniqueness on both sides.
    # If user is deleted → delete their cart too (CASCADE).
    # related_name='cart': access with user.cart (not user.cart_set)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_items(self):
        """Total number of items (counting quantities) in this cart."""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        """Sum of (item.product.effective_price × item.quantity) for all items."""
        return sum(item.subtotal for item in self.items.all())

    def __str__(self):
        return f"Cart of {self.user.username} ({self.total_items} items)"

    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'


# ─────────────────────────────────────────────────────────────
# MODEL 6: CartItem
# ─────────────────────────────────────────────────────────────
class CartItem(models.Model):
    """
    One row per product in the cart.
    Example: Cart has 2 CartItems → User wants 2 different products.
    If they want 3 of the same product, quantity=3, not 3 rows.
    """

    # Which cart this item belongs to.
    # related_name='items': access with cart.items.all()
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # Which product was added.
    # SET_NULL: if the product is deleted from the store, the cart item
    # remains (so the customer knows it was there) but product becomes null.
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )

    # How many of this product the user wants to buy.
    # PositiveIntegerField: enforces value > 0 at the database level.
    quantity = models.PositiveIntegerField(default=1)

    added_at = models.DateTimeField(auto_now_add=True)

    @property
    def subtotal(self):
        """Price × quantity for this single cart item line."""
        return self.product.effective_price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.cart.user.username}'s cart"

    class Meta:
        # Prevent the same product from appearing twice in one cart.
        # If user clicks "Add to Cart" again, we increase quantity instead.
        unique_together = ('cart', 'product')
        ordering = ['-added_at']
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
