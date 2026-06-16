from django.urls import path
from .views import (
    PlaceOrderView,
    OrderListView,
    OrderDetailView,
    CancelOrderView,
    AdminOrderListView,
    AdminOrderDetailView,
    AdminOrderAnalyticsView,
)

# All URLs prefixed with /api/orders/ (set in backend/urls.py)
urlpatterns = [

    # ── Customer Order Endpoints ───────────────────────────────────────────────

    # List my orders / Place a new order
    # GET  /api/orders/        → my order history
    path('',         OrderListView.as_view(),   name='order_list'),

    # Create order from cart
    # POST /api/orders/create/ → checkout
    path('create/',  PlaceOrderView.as_view(),  name='order_create'),

    # ── Admin Endpoints ────────────────────────────────────────────────────────
    # IMPORTANT: admin/ routes must come BEFORE <int:pk>/ so 'admin' is not
    # mistakenly parsed as a product ID.

    # Admin: list all orders + analytics
    path('admin/',             AdminOrderListView.as_view(),     name='admin_order_list'),
    path('admin/analytics/',   AdminOrderAnalyticsView.as_view(), name='admin_order_analytics'),
    path('admin/<int:pk>/',    AdminOrderDetailView.as_view(),   name='admin_order_detail'),

    # ── Per-Order Endpoints ────────────────────────────────────────────────────

    # Single order detail (customer views their own)
    # GET /api/orders/<pk>/
    path('<int:pk>/',         OrderDetailView.as_view(),  name='order_detail'),

    # Cancel an order (customer only, pending/confirmed only)
    # POST /api/orders/<pk>/cancel/
    path('<int:pk>/cancel/',  CancelOrderView.as_view(),  name='order_cancel'),
]
