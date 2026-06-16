from rest_framework import serializers
from .models import Category, Product, ProductImage, Recommendation


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 1: CategorySerializer
# Used for: GET /api/categories/ and nested inside products
# ─────────────────────────────────────────────────────────────────────────────
class CategorySerializer(serializers.ModelSerializer):
    """
    Serializes a category.
    'product_count' is a computed field — counts how many products are in this category.
    """

    # SerializerMethodField: value is returned by get_product_count() below
    product_count = serializers.SerializerMethodField()
    image_url     = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'image_url',
                  'product_count', 'created_at']
        read_only_fields = ['id', 'slug', 'product_count', 'image_url', 'created_at']
        extra_kwargs = {
            'image': {'write_only': True, 'required': False},
        }

    def get_product_count(self, obj):
        """
        obj is the Category instance.
        obj.products is the reverse relation from Product (related_name='products').
        .filter(is_available=True) counts only available products.
        """
        return obj.products.filter(is_available=True).count()

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def validate_name(self, value):
        """Prevent duplicate category names (case-insensitive)."""
        qs = Category.objects.filter(name__iexact=value)
        # Exclude the current instance when updating so it doesn't flag itself
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 2: ProductImageSerializer
# Used for: nested inside products AND the image upload endpoint
# ─────────────────────────────────────────────────────────────────────────────
class ProductImageSerializer(serializers.ModelSerializer):
    """Serializes a single product image."""

    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = ProductImage
        fields = ['id', 'image', 'image_url', 'is_primary', 'alt_text', 'uploaded_at']
        read_only_fields = ['id', 'image_url', 'uploaded_at']
        extra_kwargs = {
            'image': {'write_only': True},
        }

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 3: ProductListSerializer
# Used for: GET /api/products/ (list view — lightweight, fast)
# ─────────────────────────────────────────────────────────────────────────────
class ProductListSerializer(serializers.ModelSerializer):
    """
    Lightweight product serializer for the list/grid view.

    We deliberately OMIT full description and all images except the primary one.
    Reason: A product grid shows 12 products at a time. If each product
    returned its full description (potentially 2000 chars) and all 5 images,
    the response payload would be 10x larger than needed — slow to transfer
    and slow to render in React.

    The full detail is loaded only when the user clicks a specific product.
    """

    # Nest the category inside the product response
    # so the frontend gets: { "category": { "id": 1, "name": "Electronics" } }
    # instead of just: { "category": 1 }
    category = CategorySerializer(read_only=True)

    # Computed fields
    primary_image_url  = serializers.SerializerMethodField()
    effective_price    = serializers.SerializerMethodField()
    discount_percent   = serializers.SerializerMethodField()
    is_on_sale         = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'category',
            'price', 'discount_price', 'effective_price',
            'discount_percent', 'is_on_sale',
            'stock', 'is_available',
            'rating', 'rating_count',
            'primary_image_url',
            'created_at',
        ]

    def get_primary_image_url(self, obj):
        """
        Returns the URL of the primary image, or the first image, or None.
        'obj.primary_image' is the property we defined on the Product model.
        """
        request = self.context.get('request')
        img = obj.primary_image  # Uses the @property from models.py
        if img and request:
            return request.build_absolute_uri(img.image.url)
        return None

    def get_effective_price(self, obj):
        """The price the customer actually pays (discount if available)."""
        return str(obj.effective_price)  # str() to preserve decimal precision

    def get_discount_percent(self, obj):
        """
        Calculates the percentage discount.
        E.g. original=100, discounted=75 → 25% off
        Returns None if there's no discount.
        """
        if obj.discount_price and obj.price > 0:
            percent = ((obj.price - obj.discount_price) / obj.price) * 100
            return round(percent)
        return None

    def get_is_on_sale(self, obj):
        return obj.is_on_sale  # Uses the @property from models.py


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 4: ProductDetailSerializer
# Used for: GET /api/products/<id>/ (single product — full details)
# ─────────────────────────────────────────────────────────────────────────────
class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Full product serializer for the product detail page.
    Includes all images, full description, and all computed fields.
    """

    category    = CategorySerializer(read_only=True)
    images      = ProductImageSerializer(many=True, read_only=True)

    primary_image_url = serializers.SerializerMethodField()
    effective_price   = serializers.SerializerMethodField()
    discount_percent  = serializers.SerializerMethodField()
    is_on_sale        = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'category',
            'description',
            'price', 'discount_price', 'effective_price',
            'discount_percent', 'is_on_sale',
            'stock', 'is_available',
            'rating', 'rating_count',
            'images', 'primary_image_url',
            'created_at', 'updated_at',
        ]

    def get_primary_image_url(self, obj):
        request = self.context.get('request')
        img = obj.primary_image
        if img and request:
            return request.build_absolute_uri(img.image.url)
        return None

    def get_effective_price(self, obj):
        return str(obj.effective_price)

    def get_discount_percent(self, obj):
        if obj.discount_price and obj.price > 0:
            percent = ((obj.price - obj.discount_price) / obj.price) * 100
            return round(percent)
        return None

    def get_is_on_sale(self, obj):
        return obj.is_on_sale


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 5: ProductCreateUpdateSerializer
# Used for: POST, PUT, PATCH on /api/products/ (admin only)
# ─────────────────────────────────────────────────────────────────────────────
class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Used by admins to create and update products.

    Input: accepts category as an ID (integer)
    Output: returns the full product detail via ProductDetailSerializer

    We use a separate serializer for input vs output because:
      - Input: category=1 (just the ID — easy to send from a form)
      - Output: category={id:1, name:"Electronics"} (full object — useful for display)
    """

    # PrimaryKeyRelatedField accepts an integer ID and resolves it to a Category instance
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model  = Product
        fields = [
            'name', 'category', 'description',
            'price', 'discount_price',
            'stock', 'is_available',
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_discount_price(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Discount price must be greater than zero.")
        return value

    def validate(self, attrs):
        price = attrs.get('price') or (self.instance.price if self.instance else None)
        discount = attrs.get('discount_price')
        if discount and price and discount >= price:
            raise serializers.ValidationError(
                {"discount_price": "Discount price must be less than the regular price."}
            )
        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 6: RecommendationSerializer
# Used for: GET /api/recommendations/ (Phase 15)
# ─────────────────────────────────────────────────────────────────────────────
class RecommendationSerializer(serializers.ModelSerializer):
    """Serializes an AI recommendation with the product details embedded."""
    product = ProductListSerializer(read_only=True)

    class Meta:
        model  = Recommendation
        fields = ['id', 'product', 'score', 'reason', 'created_at']
