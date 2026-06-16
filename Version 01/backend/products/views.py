from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.pagination import PageNumberPagination

from .models import Category, Product, ProductImage, Recommendation
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    ProductImageSerializer,
    RecommendationSerializer,
)
from utils.responses import success_response, error_response, paginated_response
from utils.permissions import IsAdminUser, IsAuthenticatedOrReadOnly


# ─── Pagination helper ────────────────────────────────────────────────────────
class ProductPagination(PageNumberPagination):
    """
    Custom paginator for product lists.
    Allows the client to control page size via ?page_size=24 (up to 48).
    Defaults to 12 (the global PAGE_SIZE from settings.py).
    """
    page_size              = 12
    page_size_query_param  = 'page_size'
    max_page_size          = 48


# ═════════════════════════════════════════════════════════════════════════════
# CATEGORY VIEWS
# ═════════════════════════════════════════════════════════════════════════════

class CategoryListCreateView(APIView):
    """
    GET  /api/categories/ → List all categories (public)
    POST /api/categories/ → Create a new category (admin only)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        """
        get_permissions() is called by DRF to determine which permission
        classes apply to the current request.

        We use it here to apply different permissions per HTTP method:
          - GET  → AllowAny (anyone can see categories)
          - POST → IsAdminUser (only admins can create)

        This is cleaner than using separate view classes for public vs admin.
        """
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]

    def get(self, request):
        categories = Category.objects.all().order_by('name')
        serializer = CategorySerializer(
            categories,
            many=True,
            context={'request': request}
        )
        return success_response(
            data=serializer.data,
            message=f"{categories.count()} categories found."
        )

    def post(self, request):
        serializer = CategorySerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return error_response(
                message="Category creation failed.",
                errors=serializer.errors
            )
        serializer.save()
        return success_response(
            data=serializer.data,
            message="Category created successfully.",
            status_code=201
        )


class CategoryDetailView(APIView):
    """
    GET    /api/categories/<pk>/ → Category detail + its products (public)
    PUT    /api/categories/<pk>/ → Update category (admin only)
    PATCH  /api/categories/<pk>/ → Partial update (admin only)
    DELETE /api/categories/<pk>/ → Delete category (admin only)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def _get_category(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        category = self._get_category(pk)
        if not category:
            return error_response(message="Category not found.", status_code=404)

        cat_data   = CategorySerializer(category, context={'request': request}).data

        # Also return the products in this category (paginated)
        products   = Product.objects.filter(
            category=category, is_available=True
        ).select_related('category').prefetch_related('images')

        paginator  = ProductPagination()
        page       = paginator.paginate_queryset(products, request)
        prod_data  = ProductListSerializer(page, many=True, context={'request': request}).data

        return success_response(data={
            'category': cat_data,
            'products': prod_data,
            'count':    paginator.page.paginator.count,
            'next':     paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
        })

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        category = self._get_category(pk)
        if not category:
            return error_response(message="Category not found.", status_code=404)

        serializer = CategorySerializer(
            category,
            data=request.data,
            partial=partial,
            context={'request': request}
        )
        if not serializer.is_valid():
            return error_response(message="Update failed.", errors=serializer.errors)

        serializer.save()
        return success_response(data=serializer.data, message="Category updated successfully.")

    def delete(self, request, pk):
        category = self._get_category(pk)
        if not category:
            return error_response(message="Category not found.", status_code=404)

        name = category.name
        category.delete()
        return success_response(message=f"Category '{name}' deleted successfully.")


# ═════════════════════════════════════════════════════════════════════════════
# PRODUCT VIEWS
# ═════════════════════════════════════════════════════════════════════════════

class ProductListCreateView(APIView):
    """
    GET  /api/products/ → List all products with search, filter, sort (public)
    POST /api/products/ → Create a product (admin only)

    Query Parameters for GET:
      ?q=<text>          → search name and description
      ?category=<id>     → filter by category ID
      ?min_price=<num>   → filter products >= min_price
      ?max_price=<num>   → filter products <= max_price
      ?available=true    → only show in-stock products
      ?on_sale=true      → only show discounted products
      ?sort=<option>     → newest | price_asc | price_desc | rating
      ?page=<n>          → page number
      ?page_size=<n>     → results per page (max 48)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [AllowAny()]

    def get(self, request):
        # Start with all available products
        # select_related('category')  → avoids N+1 queries for category name
        # prefetch_related('images')  → avoids N+1 queries for images
        queryset = Product.objects.select_related('category').prefetch_related('images')

        # ── Search ───────────────────────────────────────────────────────────
        # ?q=shoes → searches name and description simultaneously
        q = request.query_params.get('q', '').strip()
        if q:
            # Q objects let us combine multiple filter conditions with OR (|)
            # __icontains = case-insensitive "contains"
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
            )

        # ── Filter by Category ────────────────────────────────────────────────
        # ?category=3 → only show products where category_id = 3
        category_id = request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # ── Filter by Price Range ────────────────────────────────────────────
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass  # Ignore invalid price values silently
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass

        # ── Filter by Availability ───────────────────────────────────────────
        available = request.query_params.get('available', '').lower()
        if available == 'true':
            queryset = queryset.filter(is_available=True, stock__gt=0)

        # ── Filter: Only On-Sale Products ────────────────────────────────────
        on_sale = request.query_params.get('on_sale', '').lower()
        if on_sale == 'true':
            # isnull=False means discount_price is NOT null (i.e., it has a value)
            queryset = queryset.filter(discount_price__isnull=False)

        # ── Sorting ───────────────────────────────────────────────────────────
        sort = request.query_params.get('sort', 'newest')
        sort_options = {
            'newest':     '-created_at',     # Most recently added first
            'oldest':     'created_at',
            'price_asc':  'price',            # Cheapest first
            'price_desc': '-price',           # Most expensive first
            'rating':     '-rating',          # Highest rated first
            'name_asc':   'name',
            'name_desc':  '-name',
        }
        order_by = sort_options.get(sort, '-created_at')
        queryset = queryset.order_by(order_by)

        # ── Pagination ────────────────────────────────────────────────────────
        paginator = ProductPagination()
        page      = paginator.paginate_queryset(queryset, request)

        serializer = ProductListSerializer(
            page,
            many=True,
            context={'request': request}
        )

        return paginated_response(
            paginator=paginator,
            data=serializer.data,
            message=f"Products retrieved successfully."
        )

    def post(self, request):
        """Create a new product. Admin only."""
        serializer = ProductCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Product creation failed.",
                errors=serializer.errors
            )
        product = serializer.save()

        # Return full detail (with images, computed fields) after creating
        detail_serializer = ProductDetailSerializer(
            product, context={'request': request}
        )
        return success_response(
            data=detail_serializer.data,
            message="Product created successfully.",
            status_code=201
        )


class ProductDetailView(APIView):
    """
    GET    /api/products/<pk>/ → Product detail (public)
    PUT    /api/products/<pk>/ → Full update (admin only)
    PATCH  /api/products/<pk>/ → Partial update (admin only)
    DELETE /api/products/<pk>/ → Delete (admin only)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def _get_product(self, pk):
        try:
            return Product.objects.select_related('category').prefetch_related('images').get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self._get_product(pk)
        if not product:
            return error_response(message="Product not found.", status_code=404)

        serializer = ProductDetailSerializer(product, context={'request': request})
        return success_response(
            data=serializer.data,
            message="Product retrieved successfully."
        )

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        product = self._get_product(pk)
        if not product:
            return error_response(message="Product not found.", status_code=404)

        serializer = ProductCreateUpdateSerializer(
            product, data=request.data, partial=partial
        )
        if not serializer.is_valid():
            return error_response(message="Update failed.", errors=serializer.errors)

        serializer.save()

        detail = ProductDetailSerializer(product, context={'request': request})
        return success_response(data=detail.data, message="Product updated successfully.")

    def delete(self, request, pk):
        product = self._get_product(pk)
        if not product:
            return error_response(message="Product not found.", status_code=404)

        name = product.name
        product.delete()
        return success_response(message=f"Product '{name}' deleted successfully.")


class ProductImageView(APIView):
    """
    POST   /api/products/<pk>/images/           → Upload image (admin only)
    DELETE /api/products/<pk>/images/<img_id>/  → Delete image (admin only)
    """
    permission_classes = [IsAdminUser]
    parser_classes     = [MultiPartParser, FormParser]

    def _get_product(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def post(self, request, pk):
        """Upload one or more images for a product."""
        product = self._get_product(pk)
        if not product:
            return error_response(message="Product not found.", status_code=404)

        # request.FILES is a dict of uploaded files.
        # getlist('images') gets all files uploaded under the key 'images'
        # (supports multiple files in one request).
        images = request.FILES.getlist('images')
        if not images:
            return error_response(
                message="No images provided. Send files under the key 'images'.",
                status_code=400
            )

        created_images = []
        is_primary     = not product.images.exists()  # First image is auto-primary

        for i, image_file in enumerate(images):
            img = ProductImage.objects.create(
                product    = product,
                image      = image_file,
                is_primary = is_primary if i == 0 else False,
                alt_text   = request.data.get('alt_text', product.name)
            )
            created_images.append(img)

        serializer = ProductImageSerializer(
            created_images,
            many=True,
            context={'request': request}
        )
        return success_response(
            data=serializer.data,
            message=f"{len(created_images)} image(s) uploaded successfully.",
            status_code=201
        )

    def delete(self, request, pk, img_id):
        """Delete a specific image from a product."""
        try:
            image = ProductImage.objects.get(pk=img_id, product_id=pk)
        except ProductImage.DoesNotExist:
            return error_response(message="Image not found.", status_code=404)

        was_primary = image.is_primary
        image.image.delete(save=False)   # Delete the actual file from disk
        image.delete()                   # Delete the database record

        # If we deleted the primary image, promote the first remaining image
        if was_primary:
            next_image = ProductImage.objects.filter(product_id=pk).first()
            if next_image:
                next_image.is_primary = True
                next_image.save()

        return success_response(message="Image deleted successfully.")


class SetPrimaryImageView(APIView):
    """
    PATCH /api/products/<pk>/images/<img_id>/set-primary/
    Marks a specific image as the primary image for the product.
    """
    permission_classes = [IsAdminUser]

    def patch(self, request, pk, img_id):
        try:
            image = ProductImage.objects.get(pk=img_id, product_id=pk)
        except ProductImage.DoesNotExist:
            return error_response(message="Image not found.", status_code=404)

        # Unset primary on all other images for this product
        ProductImage.objects.filter(product_id=pk).update(is_primary=False)
        image.is_primary = True
        image.save()

        return success_response(message="Primary image updated successfully.")


class FeaturedProductsView(APIView):
    """
    GET /api/products/featured/
    Returns on-sale and top-rated products for the homepage hero section.
    Public — no authentication required.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # On-sale products (have a discount price set)
        on_sale = Product.objects.filter(
            is_available=True,
            discount_price__isnull=False,
            stock__gt=0
        ).select_related('category').prefetch_related('images').order_by('-rating')[:8]

        # Top rated products
        top_rated = Product.objects.filter(
            is_available=True,
            rating__gte=4.0,
            stock__gt=0
        ).select_related('category').prefetch_related('images').order_by('-rating')[:8]

        # Newest arrivals
        newest = Product.objects.filter(
            is_available=True,
            stock__gt=0
        ).select_related('category').prefetch_related('images').order_by('-created_at')[:8]

        context = {'request': request}
        return success_response(data={
            'on_sale':   ProductListSerializer(on_sale,   many=True, context=context).data,
            'top_rated': ProductListSerializer(top_rated, many=True, context=context).data,
            'newest':    ProductListSerializer(newest,    many=True, context=context).data,
        }, message="Featured products retrieved.")


class AdminProductListView(APIView):
    """
    GET /api/products/admin/all/
    Returns ALL products (including unavailable) for the admin dashboard.
    Admin only.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        queryset  = Product.objects.select_related('category').prefetch_related('images').order_by('-created_at')
        paginator = ProductPagination()
        page      = paginator.paginate_queryset(queryset, request)
        serializer = ProductListSerializer(page, many=True, context={'request': request})
        return paginated_response(paginator, serializer.data, "All products retrieved.")


class RecommendationView(APIView):
    """
    GET /api/products/recommendations/
    Returns AI-generated product recommendations for the logged-in user.
    Falls back to top-rated products if no recommendations exist yet.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recommendations = Recommendation.objects.filter(
            user=request.user
        ).select_related('product__category').prefetch_related('product__images').order_by('-score')[:10]

        if recommendations.exists():
            serializer = RecommendationSerializer(
                recommendations, many=True, context={'request': request}
            )
            return success_response(
                data=serializer.data,
                message="Personalized recommendations loaded."
            )

        # Fallback: show top-rated products when no recommendations exist
        fallback = Product.objects.filter(
            is_available=True, stock__gt=0
        ).select_related('category').prefetch_related('images').order_by('-rating')[:10]

        serializer = ProductListSerializer(fallback, many=True, context={'request': request})
        return success_response(
            data=serializer.data,
            message="Top-rated products (recommendations coming soon)."
        )
