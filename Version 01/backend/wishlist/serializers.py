from rest_framework import serializers
from .models import Wishlist
from products.models import Product
from products.serializers import ProductListSerializer


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 1: WishlistSerializer
# Used for: GET /api/wishlist/
# ─────────────────────────────────────────────────────────────────────────────
class WishlistSerializer(serializers.ModelSerializer):
    """
    Serializes a single wishlist entry.
    Nests the full product so the frontend can render product cards
    in the wishlist page without extra API calls.
    """

    product = ProductListSerializer(read_only=True)

    class Meta:
        model  = Wishlist
        fields = ['id', 'product', 'added_at']
        read_only_fields = fields


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 2: AddToWishlistSerializer
# Used for: POST /api/wishlist/add/
# ─────────────────────────────────────────────────────────────────────────────
class AddToWishlistSerializer(serializers.Serializer):
    """
    Validates the request to add a product to the wishlist.
    Input: { "product_id": 5 }
    """

    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        """Ensure the product exists before adding to wishlist."""
        try:
            product = Product.objects.get(pk=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found.")

        # Attach product object for use in the view
        self.product = product
        return value
