from django.db import models
from django.conf import settings
from django.utils.text import slugify


# ─────────────────────────────────────────────────────────────
# MODEL 2: Category
# ─────────────────────────────────────────────────────────────
class Category(models.Model):
    """
    Represents a product category (e.g., Electronics, Clothing, Books).
    Products are organized into categories for browsing and filtering.
    """

    # The category name shown to users (e.g., "Electronics").
    # max_length=100 means the database column can store up to 100 characters.
    # unique=True prevents two categories with the same name.
    name = models.CharField(max_length=100, unique=True)

    # A slug is a URL-friendly version of the name.
    # Example: "Men's Clothing" → "mens-clothing"
    # Used in URLs like /products/?category=mens-clothing
    # blank=True so we can auto-generate it in the save() method.
    slug = models.SlugField(unique=True, blank=True)

    # A longer description shown on the category page.
    # blank=True makes it optional.
    description = models.TextField(blank=True)

    # Optional category image (e.g., a banner or icon).
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    # Timestamps — auto-set by Django, cannot be changed manually.
    created_at = models.DateTimeField(auto_now_add=True)  # Set once, at creation
    updated_at = models.DateTimeField(auto_now=True)      # Updated on every save

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if not provided.
        # slugify("Men's Clothing") → "mens-clothing"
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


# ─────────────────────────────────────────────────────────────
# MODEL 3: Product
# ─────────────────────────────────────────────────────────────
class Product(models.Model):
    """
    Represents a product for sale in the store.
    Each product belongs to one category.
    """

    # ForeignKey creates a many-to-one relationship:
    #   Many products → one category.
    # on_delete=models.SET_NULL: if the category is deleted, the product
    #   stays but its category field becomes NULL (not deleted too).
    # null=True, blank=True: allows a product to have no category.
    # related_name='products': lets us write category.products.all()
    #   to get all products in a category (reverse lookup).
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    # Product name (e.g., "Nike Air Max 270").
    name = models.CharField(max_length=200)

    # URL-friendly unique identifier for this product.
    # Used in URLs: /products/nike-air-max-270/
    slug = models.SlugField(unique=True, blank=True)

    # Full product description (HTML or plain text).
    description = models.TextField()

    # Price uses DecimalField for precise money arithmetic.
    # FloatField would cause rounding errors (e.g., 19.99 + 0.01 = 20.000000001).
    # max_digits=10: up to 10 total digits (e.g., 9999999.99)
    # decimal_places=2: exactly 2 decimal places (cents)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Optional discounted price. If set, show crossed-out original price.
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    # How many units are in stock.
    stock = models.PositiveIntegerField(default=0)

    # If False, the product is hidden from customers even if in stock.
    is_available = models.BooleanField(default=True)

    # Average rating (0.0 to 5.0). Updated when reviews are added.
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )

    # How many times this product has been rated.
    rating_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # If two products share a name, the slug would collide.
            # We add the pk (primary key) to ensure uniqueness.
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        """Returns the discount price if available, otherwise the regular price."""
        return self.discount_price if self.discount_price else self.price

    @property
    def is_on_sale(self):
        """True if this product has a discounted price."""
        return self.discount_price is not None

    @property
    def primary_image(self):
        """Returns the primary image, or first image, or None."""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'


# ─────────────────────────────────────────────────────────────
# MODEL 4: ProductImage
# ─────────────────────────────────────────────────────────────
class ProductImage(models.Model):
    """
    A product can have multiple images (gallery).
    One image is marked as primary and shown as the main/thumbnail image.
    """

    # ForeignKey to Product.
    # on_delete=CASCADE: if the product is deleted, all its images are too.
    # related_name='images': lets us write product.images.all()
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )

    # The actual image file. Stored in media/products/ folder.
    image = models.ImageField(upload_to='products/')

    # Marks which image is the main/thumbnail image.
    # The admin can mark one image per product as primary.
    is_primary = models.BooleanField(default=False)

    # Alt text for accessibility and SEO.
    alt_text = models.CharField(max_length=200, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name} ({'primary' if self.is_primary else 'secondary'})"

    class Meta:
        ordering = ['-is_primary', 'uploaded_at']
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'


# ─────────────────────────────────────────────────────────────
# MODEL 12: Recommendation
# ─────────────────────────────────────────────────────────────
class Recommendation(models.Model):
    """
    Stores AI-generated product recommendations for each user.
    The recommendation engine (Phase 15) computes scores and writes here.
    The React frontend reads from here to display "Recommended for You".
    """

    # settings.AUTH_USER_MODEL is the correct way to reference the User model
    # from other apps. Never import User directly to avoid circular imports.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='recommended_to'
    )

    # The higher the score, the more relevant the recommendation.
    # Range: 0.0 (irrelevant) to 1.0 (perfect match).
    score = models.FloatField(default=0.0)

    # A human-readable explanation of why this product was recommended.
    # Shown below the product card: "Based on your recent purchases"
    reason = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation: {self.product.name} for {self.user.username} (score: {self.score:.2f})"

    class Meta:
        # One recommendation entry per (user, product) pair.
        # Prevents duplicate recommendations for the same product to the same user.
        unique_together = ('user', 'product')
        ordering = ['-score']
        verbose_name = 'Recommendation'
        verbose_name_plural = 'Recommendations'
