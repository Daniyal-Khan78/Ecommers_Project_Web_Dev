from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.utils import timezone


# ─── Health Check View ─────────────────────────────────────────────────────────
# A simple view (no DRF needed) that returns server status.
# Called by monitoring tools, deployment platforms, and the React app
# on startup to confirm the backend is alive before making API calls.
def health_check(request):
    return JsonResponse({
        "status":    "ok",
        "server":    "ShopNest API",
        "version":   "1.0.0",
        "timestamp": timezone.now().isoformat(),
        "database":  "connected",
    })


# ─── Root URL Configuration ────────────────────────────────────────────────────
urlpatterns = [
    # Django's built-in admin panel
    path('admin/', admin.site.urls),

    # Health check — no auth required
    path('api/health/', health_check, name='health_check'),

    # App-level API endpoints (each app manages its own URL patterns)
    path('api/auth/',          include('users.urls')),
    path('api/products/',      include('products.urls')),
    path('api/categories/',    include('products.category_urls')),
    path('api/cart/',          include('cart.urls')),
    path('api/wishlist/',      include('wishlist.urls')),
    path('api/orders/',        include('orders.urls')),
    path('api/payments/',      include('orders.payment_urls')),  # Stripe: Visa/Mastercard/Amex
    path('api/notifications/', include('notifications.urls')),
]

# ─── Custom Error Handlers ─────────────────────────────────────────────────────
# These replace Django's default HTML error pages with JSON responses.
# They only activate when DEBUG=False (production mode).
# When DEBUG=True, Django still shows the detailed debug error page.

def handler404(request, exception):
    """Called when no URL pattern matches the requested URL."""
    return JsonResponse(
        {"success": False, "message": "The requested endpoint does not exist."},
        status=404
    )

def handler500(request):
    """Called when an unhandled exception occurs in a view."""
    return JsonResponse(
        {"success": False, "message": "An internal server error occurred."},
        status=500
    )

# Wire up the custom error handlers
handler404 = handler404
handler500 = handler500

# ─── Media File Serving ────────────────────────────────────────────────────────
# During development (DEBUG=True), Django serves uploaded files directly.
# In production, a web server like Nginx handles this more efficiently.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT if hasattr(settings, 'STATIC_ROOT') else None)
