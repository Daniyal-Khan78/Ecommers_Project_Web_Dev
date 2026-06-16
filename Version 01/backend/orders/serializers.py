from rest_framework import serializers
from .models import Order, OrderItem, Payment
from products.serializers import ProductListSerializer


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 1: PaymentSerializer
# Used nested inside OrderSerializer to show payment details
# ─────────────────────────────────────────────────────────────────────────────
class PaymentSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for payment information displayed alongside an order.
    The customer sees: payment method, status, and when it was paid.
    """
    class Meta:
        model  = Payment
        fields = [
            'id', 'payment_method', 'amount', 'status',
            'stripe_payment_id', 'paid_at', 'created_at'
        ]
        read_only_fields = fields


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 2: OrderItemSerializer
# Used nested inside OrderSerializer for the list of purchased products
# ─────────────────────────────────────────────────────────────────────────────
class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializes one line of an order.

    We embed the full product info (name, image) so the order detail page
    can show product cards even if the product was later deleted from the store.

    KEY DESIGN: 'price' here is the SNAPSHOT price stored on OrderItem,
    NOT the current product price. This is what the customer actually paid.
    """
    # Nested product — read-only because order items are never changed after creation
    product  = ProductListSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model  = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'subtotal']
        read_only_fields = fields

    def get_subtotal(self, obj):
        """price × quantity for this order line."""
        return str(obj.price * obj.quantity)


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 3: OrderSerializer
# Used for: order list and order detail responses
# ─────────────────────────────────────────────────────────────────────────────
class OrderSerializer(serializers.ModelSerializer):
    """
    Full order serializer including all items and payment details.

    For the order list, this is slightly heavy (nested items + payment).
    If performance becomes an issue, we could create a lighter OrderListSerializer.
    But for a course project, this is clean and complete.
    """
    items   = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)

    # Human-readable status label (e.g., "Shipped" instead of "shipped")
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model  = Order
        fields = [
            'id', 'status', 'status_display',
            'total_amount', 'shipping_address', 'notes',
            'items', 'payment',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 4: PlaceOrderSerializer
# Used for: POST /api/orders/create/
# ─────────────────────────────────────────────────────────────────────────────
class PlaceOrderSerializer(serializers.Serializer):
    """
    Validates the checkout request before the order is placed.

    The customer sends:
      - shipping_address: where to deliver
      - payment_method:   'stripe' or 'cod' (cash on delivery)
      - notes:            optional delivery notes

    The cart contents come from the database (not from the request),
    so the customer cannot manipulate prices by sending fake cart data.
    """

    shipping_address = serializers.CharField(
        min_length=10,
        error_messages={'min_length': 'Please enter a complete shipping address (at least 10 characters).'}
    )

    payment_method = serializers.ChoiceField(
        choices=Payment.Method.choices,
        default=Payment.Method.COD
    )

    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_shipping_address(self, value):
        """Strip extra whitespace from the address."""
        return value.strip()


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 5: OrderStatusUpdateSerializer
# Used for: PATCH /api/orders/admin/<pk>/ — admin updates order status
# ─────────────────────────────────────────────────────────────────────────────
class OrderStatusUpdateSerializer(serializers.Serializer):
    """
    Validates the new status value sent by an admin.

    Uses ChoiceField to enforce that only valid status transitions are accepted.
    We could add more complex transition logic here (e.g., can't go from
    'delivered' back to 'pending'), but ChoiceField is sufficient for this project.
    """
    status = serializers.ChoiceField(choices=Order.Status.choices)
    notes  = serializers.CharField(required=False, allow_blank=True)
