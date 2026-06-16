from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product
from products.serializers import ProductListSerializer


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 1: CartItemSerializer
# Used for: displaying individual items inside the cart response
# ─────────────────────────────────────────────────────────────────────────────
class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializes one line in the cart (one product + quantity).

    Nests a full ProductListSerializer so the frontend gets the
    product name, image, price, and availability without a second request.

    subtotal is a computed field: effective_price × quantity.
    """

    # Nested serializer — returns the full product object, not just its ID.
    # read_only=True because we never accept product data from the client here;
    # we only accept product_id (handled in AddToCartSerializer).
    product = ProductListSerializer(read_only=True)

    # Computed field: price × quantity for this cart line
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model  = CartItem
        fields = ['id', 'product', 'quantity', 'subtotal', 'added_at']
        read_only_fields = ['id', 'subtotal', 'added_at']

    def get_subtotal(self, obj):
        """
        obj.product.effective_price → discount_price if set, else price.
        We multiply by quantity to get the line total.
        Returns a string to preserve decimal precision.
        """
        return str(obj.product.effective_price * obj.quantity)


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 2: CartSerializer
# Used for: GET /api/cart/ — the full cart view
# ─────────────────────────────────────────────────────────────────────────────
class CartSerializer(serializers.ModelSerializer):
    """
    Serializes the entire cart including all items and computed totals.

    Computed fields:
      items       → all CartItem rows for this cart
      total_items → sum of all quantities (e.g., 2 shoes + 3 books = 5)
      total_price → sum of all subtotals
      savings     → how much the customer saves from discounts
    """

    # many=True: serialize a queryset (list) of CartItem objects
    items       = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    savings     = serializers.SerializerMethodField()

    class Meta:
        model  = Cart
        fields = ['id', 'items', 'total_items', 'total_price', 'savings', 'updated_at']
        read_only_fields = fields

    def get_total_items(self, obj):
        """Sum all quantities across all cart items."""
        return sum(item.quantity for item in obj.items.all())

    def get_total_price(self, obj):
        """
        Sum of (effective_price × quantity) for every item in the cart.
        effective_price uses discount_price if available, otherwise regular price.
        """
        total = sum(item.product.effective_price * item.quantity for item in obj.items.all())
        return str(total)

    def get_savings(self, obj):
        """
        How much the customer saves because of discounts.
        savings = sum of (regular_price - discount_price) × quantity, for discounted items.
        """
        total_saved = 0
        for item in obj.items.all():
            if item.product.discount_price:
                saved_per_unit = item.product.price - item.product.discount_price
                total_saved   += saved_per_unit * item.quantity
        return str(total_saved)


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 3: AddToCartSerializer
# Used for: POST /api/cart/add/
# ─────────────────────────────────────────────────────────────────────────────
class AddToCartSerializer(serializers.Serializer):
    """
    Validates the request to add a product to the cart.

    Input:  { "product_id": 5, "quantity": 2 }
    Output: (used only for validation — the view handles response)

    We use base Serializer (not ModelSerializer) because we're not
    directly creating a CartItem — we're doing logic (add OR increment).
    """

    product_id = serializers.IntegerField()
    quantity   = serializers.IntegerField(min_value=1, max_value=100, default=1)

    def validate_product_id(self, value):
        """Check the product exists and is available for purchase."""
        try:
            product = Product.objects.get(pk=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found.")

        if not product.is_available:
            raise serializers.ValidationError(
                f"'{product.name}' is currently unavailable."
            )
        if product.stock == 0:
            raise serializers.ValidationError(
                f"'{product.name}' is out of stock."
            )

        return value

    def validate(self, attrs):
        """
        Cross-field validation: check requested quantity doesn't exceed stock.
        We need both product_id and quantity, so this must be in validate()
        not validate_product_id() (which only has access to product_id alone).
        """
        product_id = attrs.get('product_id')
        quantity   = attrs.get('quantity', 1)

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return attrs  # Already caught in validate_product_id

        if quantity > product.stock:
            raise serializers.ValidationError(
                {"quantity": f"Only {product.stock} unit(s) available. You requested {quantity}."}
            )

        # Attach the product object so the view doesn't need another DB query
        attrs['product'] = product
        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 4: UpdateCartItemSerializer
# Used for: PATCH /api/cart/items/<id>/
# ─────────────────────────────────────────────────────────────────────────────
class UpdateCartItemSerializer(serializers.Serializer):
    """
    Validates a request to change the quantity of a cart item.
    Input: { "quantity": 3 }
    """

    quantity = serializers.IntegerField(min_value=1, max_value=100)

    def validate_quantity(self, value):
        """
        self.context['cart_item'] is the CartItem being updated.
        We pass it in from the view: UpdateCartItemSerializer(data, context={'cart_item': item})
        """
        cart_item = self.context.get('cart_item')
        if cart_item and value > cart_item.product.stock:
            raise serializers.ValidationError(
                f"Only {cart_item.product.stock} unit(s) available."
            )
        return value
