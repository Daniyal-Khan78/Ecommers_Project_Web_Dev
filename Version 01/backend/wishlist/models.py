from django.db import models
from django.conf import settings


# ─────────────────────────────────────────────────────────────
# MODEL 7: Wishlist
# ─────────────────────────────────────────────────────────────
class Wishlist(models.Model):
    """
    Stores products a user has saved for later (heart/bookmark feature).

    Design decision: Unlike the Cart model which has a separate Cart
    container and CartItem rows, the Wishlist uses a simpler flat design —
    each row IS one wishlist entry (user + product pair).
    This works because wishlists don't have quantities or subtotals.
    """

    # The user who saved this product.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )

    # The product that was saved.
    # CASCADE: if the product is deleted, remove it from all wishlists.
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )

    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.product.name}"

    class Meta:
        # Prevent a user from adding the same product to their wishlist twice.
        # unique_together creates a composite unique constraint:
        # the (user_id, product_id) combination must be unique.
        unique_together = ('user', 'product')
        ordering = ['-added_at']
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
