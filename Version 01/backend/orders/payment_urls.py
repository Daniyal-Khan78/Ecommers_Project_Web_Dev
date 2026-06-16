from django.urls import path
from .payment_views import (
    CreatePaymentIntentView,
    ConfirmPaymentView,
    StripeWebhookView,
    PaymentStatusView,
    AdminRefundView,
)

# All URLs prefixed with /api/payments/ (added in backend/urls.py below)
urlpatterns = [

    # Step 1: React calls this first to get a client_secret
    # Accepts Visa, Mastercard, Amex, Discover — all via Stripe
    path('create-intent/',         CreatePaymentIntentView.as_view(), name='payment_create_intent'),

    # Step 2: React calls this after Stripe processes the card on the frontend
    path('confirm/',               ConfirmPaymentView.as_view(),      name='payment_confirm'),

    # Stripe calls this automatically (async backup confirmation)
    # Must NOT require authentication — Stripe sends no JWT
    path('webhook/',               StripeWebhookView.as_view(),       name='payment_webhook'),

    # Get payment status for an order (used for 3D Secure polling)
    path('order/<int:order_id>/',  PaymentStatusView.as_view(),       name='payment_status'),

    # Admin: issue refund to original Visa/Mastercard/Amex card
    path('admin/refund/',          AdminRefundView.as_view(),         name='payment_refund'),
]
