from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    ChangePasswordView,
    VerifyEmailView,
    ResendVerificationView,
    AdminUserListView,
    AdminUserDetailView,
)

# All these URLs are prefixed with /api/auth/ (set in backend/urls.py)
urlpatterns = [

    # ── Public Auth Endpoints (no token required) ──────────────────────────────
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/',    LoginView.as_view(),    name='auth_login'),

    # TokenRefreshView is built into SimpleJWT.
    # Client sends: { "refresh": "<refresh_token>" }
    # Server returns: { "access": "<new_access_token>" }
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ── Protected Endpoints (JWT token required) ───────────────────────────────
    path('logout/',              LogoutView.as_view(),              name='auth_logout'),
    path('profile/',             ProfileView.as_view(),             name='auth_profile'),
    path('profile/update/',      ProfileView.as_view(),             name='auth_profile_update'),
    path('change-password/',     ChangePasswordView.as_view(),      name='auth_change_password'),
    path('resend-verification/', ResendVerificationView.as_view(),  name='auth_resend_verification'),

    # ── Email Verification ─────────────────────────────────────────────────────
    # <str:token> captures the signed token from the URL
    # e.g. /api/auth/verify-email/eyJ0eXAiOiJKV1QiLCJhbGci.../
    path('verify-email/<str:token>/', VerifyEmailView.as_view(), name='auth_verify_email'),

    # ── Admin Endpoints ────────────────────────────────────────────────────────
    path('admin/users/',      AdminUserListView.as_view(),         name='admin_user_list'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(),   name='admin_user_detail'),
]
