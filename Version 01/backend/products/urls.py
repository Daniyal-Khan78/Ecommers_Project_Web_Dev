from django.urls import path
from .views import (
    ProductListCreateView,
    ProductDetailView,
    ProductImageView,
    SetPrimaryImageView,
    FeaturedProductsView,
    AdminProductListView,
    RecommendationView,
)

# All URLs are prefixed with /api/products/ (set in backend/urls.py)
urlpatterns = [

    # ── Public Product Endpoints ───────────────────────────────────────────────
    # List with search + filter + sort + pagination
    # GET  /api/products/?q=shoes&category=1&sort=price_asc&page=2
    path('', ProductListCreateView.as_view(), name='product_list_create'),

    # Homepage featured/sale/top-rated sections
    # IMPORTANT: 'featured/' must come BEFORE '<int:pk>/' so Django doesn't
    # try to match "featured" as a product ID.
    path('featured/', FeaturedProductsView.as_view(), name='product_featured'),

    # AI recommendations (authenticated users)
    path('recommendations/', RecommendationView.as_view(), name='product_recommendations'),

    # Admin: all products including unavailable
    path('admin/all/', AdminProductListView.as_view(), name='product_admin_list'),

    # Single product detail / update / delete
    # <int:pk> captures the product ID from the URL (e.g., /api/products/42/)
    path('<int:pk>/', ProductDetailView.as_view(), name='product_detail'),

    # Product image management (admin only)
    path('<int:pk>/images/', ProductImageView.as_view(), name='product_image_upload'),
    path('<int:pk>/images/<int:img_id>/', ProductImageView.as_view(), name='product_image_delete'),
    path('<int:pk>/images/<int:img_id>/set-primary/', SetPrimaryImageView.as_view(), name='product_image_set_primary'),
]
