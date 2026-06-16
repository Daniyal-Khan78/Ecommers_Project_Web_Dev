from django.db import models
from django.conf import settings


# ─────────────────────────────────────────────────────────────
# MODEL 8: Order
# ─────────────────────────────────────────────────────────────
class Order(models.Model):
    """
    Represents a completed purchase. Created when the user clicks
    "Place Order" on the checkout page.

    An Order captures the state at time of purchase:
    - Who bought it (user)
    - What they paid (total_amount)
    - Where to ship it (shipping_address)
    - Current fulfillment state (status)
    """

    # TextChoice is the modern Django way to define a fixed set of choices.
    # It generates the choices list AND provides readable labels automatically.
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'       # Order placed, not yet confirmed
        CONFIRMED = 'confirmed', 'Confirmed'     # Admin confirmed the order
        SHIPPED   = 'shipped',   'Shipped'       # Package sent out for delivery
        DELIVERED = 'delivered', 'Delivered'     # Customer received the package
        CANCELLED = 'cancelled', 'Cancelled'     # Order was cancelled

    # The customer who placed this order.
    # SET_NULL: if the user account is deleted, keep the order record
    # (important for accounting and order history).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )

    # The delivery status. Uses the TextChoices defined above.
    # default=Status.PENDING: every new order starts as "pending".
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    # The total amount charged. Stored separately from the cart because:
    # 1. Product prices can change after purchase
    # 2. Discounts and coupons may have been applied at checkout
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Where to ship the order. Stored as plain text snapshot.
    # We don't link to the user's current address because they might
    # change their address later and we need the original.
    shipping_address = models.TextField()

    # Optional note from the customer (e.g., "Leave at door").
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.pk} by {self.user.username if self.user else 'Deleted User'} — {self.status}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'


# ─────────────────────────────────────────────────────────────
# MODEL 9: OrderItem
# ─────────────────────────────────────────────────────────────
class OrderItem(models.Model):
    """
    One row per product line in an order.
    Example: Order #5 has 2 OrderItems → customer bought 2 different products.

    IMPORTANT: We store price here (not just a link to the product) because
    product prices can change over time. The OrderItem preserves the exact
    price at the time of purchase — critical for receipts and disputes.
    """

    # Which order this line belongs to.
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # Which product was purchased.
    # SET_NULL: if the product is deleted from the store, keep the order
    # history (don't cascade delete the customer's purchase record).
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )

    # Quantity of this product purchased.
    quantity = models.PositiveIntegerField()

    # The price PER UNIT at the time of purchase.
    # This is a snapshot — it does NOT change if the product price changes later.
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        """Total for this line: price × quantity."""
        return self.price * self.quantity

    def __str__(self):
        product_name = self.product.name if self.product else 'Deleted Product'
        return f"{self.quantity}x {product_name} @ {self.price} (Order #{self.order.pk})"

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'


# ─────────────────────────────────────────────────────────────
# MODEL 10: Payment
# ─────────────────────────────────────────────────────────────
class Payment(models.Model):
    """
    Records the payment transaction for an order.
    One Order → One Payment (OneToOneField).

    Stores the Stripe payment ID so we can look up the transaction
    in the Stripe dashboard and issue refunds if needed.
    """

    class Method(models.TextChoices):
        STRIPE = 'stripe', 'Stripe (Card)'
        COD    = 'cod',    'Cash on Delivery'

    class PaymentStatus(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED    = 'failed',    'Failed'
        REFUNDED  = 'refunded',  'Refunded'

    # OneToOneField: each order has exactly one payment record.
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment'
    )

    # How the customer chose to pay.
    payment_method = models.CharField(
        max_length=20,
        choices=Method.choices
    )

    # The transaction ID returned by Stripe after a successful charge.
    # We store this so we can reference it in the Stripe dashboard.
    # blank=True, null=True: not present for Cash on Delivery orders.
    stripe_payment_id = models.CharField(max_length=200, blank=True, null=True)

    # The Stripe PaymentIntent ID (used for capturing/refunding payments).
    stripe_payment_intent = models.CharField(max_length=200, blank=True, null=True)

    # The amount actually charged (should match order.total_amount).
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Current state of the payment.
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )

    # Exact timestamp when payment was confirmed. Null until payment succeeds.
    paid_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order.pk} — {self.status} ({self.payment_method})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
