from django.contrib import admin
from .models import Category, Product, ProductImage, Recommendation


# ── Category Admin ──────────────────────────────────────────
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug', 'created_at']
    list_filter   = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}  # Auto-fills slug as you type name


# ── Inline: show product images directly inside the Product edit page ──
class ProductImageInline(admin.TabularInline):
    """
    TabularInline displays related objects (ProductImages) in a table
    directly on the Product edit page. No need to go to a separate page.
    """
    model = ProductImage
    extra = 3           # Show 3 empty image upload slots by default
    fields = ['image', 'is_primary', 'alt_text']


# ── Product Admin ────────────────────────────────────────────
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category', 'price', 'discount_price',
                     'stock', 'is_available', 'rating', 'created_at']
    list_filter   = ['is_available', 'category', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_available', 'stock']   # Edit these fields directly in list view

    # Include the ProductImage inline so admin can upload images on the Product page
    inlines = [ProductImageInline]

    # Organize the product edit page into sections
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'slug', 'description')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'discount_price', 'stock', 'is_available')
        }),
        ('Ratings', {
            'fields': ('rating', 'rating_count'),
            'classes': ('collapse',)  # This section is collapsed by default
        }),
    )


# ── ProductImage Admin ───────────────────────────────────────
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display  = ['product', 'is_primary', 'uploaded_at']
    list_filter   = ['is_primary']
    search_fields = ['product__name']  # Double underscore = traverse ForeignKey


# ── Recommendation Admin ─────────────────────────────────────
@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display  = ['user', 'product', 'score', 'reason', 'created_at']
    list_filter   = ['created_at']
    search_fields = ['user__username', 'product__name']
    ordering      = ['-score']
