from django.contrib.auth import update_session_auth_hash
from django.core import signing
from django.core.mail import send_mail
from django.conf import settings as django_settings

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    PublicUserSerializer,
)
from utils.responses import success_response, error_response
from utils.permissions import IsAdminUser


# ─── Helper: generate JWT tokens for a user ───────────────────────────────────
def get_tokens_for_user(user):
    """
    Generates a pair of JWT tokens (refresh + access) for the given user.

    RefreshToken.for_user(user) creates a refresh token and embeds
    the user's ID inside it (as a "claim"). The access token is derived
    from the refresh token.

    Returns a plain dict so the view can include it in the response.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


# ─── Helper: send verification email ─────────────────────────────────────────
def send_verification_email(user, request):
    """
    Sends an email with a signed verification link to the user.

    django.core.signing.dumps() creates a tamper-proof token from a dict.
    The salt parameter scopes the token so it can't be reused for other purposes.
    The token expires after 24 hours (checked when verifying).

    In development (EMAIL_BACKEND = console), the email is printed to the terminal.
    In production, change EMAIL_BACKEND to SMTP to send real emails.
    """
    token = signing.dumps({'user_id': user.id}, salt='email-verification')

    # Build the full verification URL the user will click in their email.
    # The React frontend handles this URL and calls our verify API.
    verify_url = f"http://localhost:3000/verify-email/{token}"

    send_mail(
        subject='Verify your ShopNest email address',
        message=(
            f"Hello {user.first_name},\n\n"
            f"Thank you for registering at ShopNest!\n\n"
            f"Please verify your email address by clicking the link below:\n"
            f"{verify_url}\n\n"
            f"This link expires in 24 hours.\n\n"
            f"If you did not create an account, please ignore this email.\n\n"
            f"— The ShopNest Team"
        ),
        from_email=django_settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,   # Don't crash if email server is down
    )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 1: RegisterView
# POST /api/auth/register/
# ═════════════════════════════════════════════════════════════════════════════
class RegisterView(APIView):
    """
    Creates a new user account.

    Permission: AllowAny — no JWT token needed (user doesn't have one yet).
    Parser: JSONParser is default but we explicitly list it for clarity.

    Flow:
      1. Receive JSON body with user data
      2. Validate with UserRegistrationSerializer
      3. Create the user (signal auto-creates the Cart)
      4. Generate JWT tokens
      5. Send verification email
      6. Return tokens + user profile
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        # is_valid() runs all field validators and the cross-field validate()
        # raise_exception=False means we handle errors ourselves
        if not serializer.is_valid():
            return error_response(
                message="Registration failed. Please correct the errors below.",
                errors=serializer.errors,
                status_code=400
            )

        # save() calls serializer.create() which calls User.objects.create_user()
        user = serializer.save()

        # Generate JWT tokens immediately so the user is logged in right away
        tokens = get_tokens_for_user(user)

        # Send verification email (printed to console in development)
        send_verification_email(user, request)

        # Serialize the user profile for the response
        profile_data = UserProfileSerializer(user, context={'request': request}).data

        return success_response(
            data={
                'user':    profile_data,
                'tokens':  tokens,
            },
            message="Account created successfully! Please check your email to verify your address.",
            status_code=201
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 2: LoginView
# POST /api/auth/login/
# ═════════════════════════════════════════════════════════════════════════════
class LoginView(APIView):
    """
    Authenticates a user and returns JWT tokens.

    Permission: AllowAny — user doesn't have a token yet.

    Flow:
      1. Receive email + password
      2. Validate with UserLoginSerializer (which calls Django's authenticate())
      3. Generate JWT tokens
      4. Return tokens + user profile
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="Login failed. Please check your credentials.",
                errors=serializer.errors,
                status_code=400
            )

        # The validated serializer has the user attached in validated_data
        user = serializer.validated_data['user']

        tokens = get_tokens_for_user(user)
        profile_data = UserProfileSerializer(user, context={'request': request}).data

        return success_response(
            data={
                'user':   profile_data,
                'tokens': tokens,
            },
            message=f"Welcome back, {user.first_name or user.username}!"
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 3: LogoutView
# POST /api/auth/logout/
# ═════════════════════════════════════════════════════════════════════════════
class LogoutView(APIView):
    """
    Logs out the user by blacklisting their refresh token.

    Why blacklisting is necessary:
      JWTs are stateless — the server doesn't store them.
      Simply deleting the token on the frontend isn't enough because
      someone who captured the refresh token could still use it.
      Blacklisting adds the token's unique ID (jti) to a database table
      so it can never be used again, even if it hasn't expired yet.

    The client must send the refresh token in the request body.
    The access token automatically expires after 60 minutes.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return error_response(
                message="Refresh token is required.",
                status_code=400
            )

        try:
            # Load the refresh token object
            token = RefreshToken(refresh_token)
            # blacklist() adds this token's jti to the OutstandingToken blacklist table
            token.blacklist()
        except TokenError as e:
            return error_response(
                message="Invalid or expired token.",
                errors={"refresh": str(e)},
                status_code=400
            )

        return success_response(message="Successfully logged out.")


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 4: ProfileView
# GET  /api/auth/profile/        → return current user's data
# PUT  /api/auth/profile/update/ → update profile fields
# ═════════════════════════════════════════════════════════════════════════════
class ProfileView(APIView):
    """
    Handles reading and updating the authenticated user's profile.

    GET  returns full profile data.
    PUT  updates allowed fields (name, phone, address, profile_image).
    PATCH is also supported (partial update — only changed fields required).

    MultiPartParser + FormParser are required to handle file uploads.
    Without these, profile_image uploads would fail silently.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        """Return the current logged-in user's profile."""
        serializer = UserProfileSerializer(
            request.user,
            context={'request': request}
        )
        return success_response(
            data=serializer.data,
            message="Profile retrieved successfully."
        )

    def put(self, request):
        """Full update — all required fields must be sent."""
        return self._update_profile(request, partial=False)

    def patch(self, request):
        """Partial update — only send the fields you want to change."""
        return self._update_profile(request, partial=True)

    def _update_profile(self, request, partial):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=partial,
            context={'request': request}
        )

        if not serializer.is_valid():
            return error_response(
                message="Profile update failed.",
                errors=serializer.errors,
                status_code=400
            )

        serializer.save()
        return success_response(
            data=serializer.data,
            message="Profile updated successfully."
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 5: ChangePasswordView
# POST /api/auth/change-password/
# ═════════════════════════════════════════════════════════════════════════════
class ChangePasswordView(APIView):
    """
    Changes the authenticated user's password.

    Security requirements:
      1. User must provide their CURRENT password (prevents unauthorized changes
         if someone gets access to an already-logged-in browser session).
      2. New password must pass all Django password validators.
      3. New password must differ from the old one.

    After changing the password, we invalidate all existing JWT tokens
    by blacklisting the provided refresh token. This forces re-login
    on all other devices — a security best practice.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="Password change failed.",
                errors=serializer.errors,
                status_code=400
            )

        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        # check_password() hashes old_password and compares to stored hash
        if not user.check_password(old_password):
            return error_response(
                message="Current password is incorrect.",
                errors={"old_password": ["The current password you entered is wrong."]},
                status_code=400
            )

        # set_password() hashes the new password and saves it
        user.set_password(new_password)
        user.save()

        # Blacklist current refresh token so other sessions are invalidated
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass  # Token already invalid — no action needed

        # Generate new tokens for the current session
        new_tokens = get_tokens_for_user(user)

        return success_response(
            data={'tokens': new_tokens},
            message="Password changed successfully. Please save your new login details."
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 6: VerifyEmailView
# GET /api/auth/verify-email/<token>/
# ═════════════════════════════════════════════════════════════════════════════
class VerifyEmailView(APIView):
    """
    Verifies the user's email address using the signed token from the email link.

    The token was created with django.core.signing.dumps() in RegisterView.
    We use signing.loads() to decode it — if the token was tampered with
    or has expired, it raises an exception that we catch.

    The React frontend navigates to /verify-email/<token> when the user
    clicks the link. The React page then calls this API endpoint.
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            # max_age=86400 = 24 hours in seconds
            # If the token is older than 24h, SignatureExpired is raised
            data = signing.loads(token, salt='email-verification', max_age=86400)
        except signing.SignatureExpired:
            return error_response(
                message="This verification link has expired. Please request a new one.",
                status_code=400
            )
        except signing.BadSignature:
            return error_response(
                message="Invalid verification link. Please request a new one.",
                status_code=400
            )

        try:
            user = User.objects.get(id=data['user_id'])
        except User.DoesNotExist:
            return error_response(
                message="User account not found.",
                status_code=404
            )

        if user.email_verified:
            return success_response(message="Your email is already verified.")

        user.email_verified = True
        user.save()

        return success_response(
            message="Email verified successfully! You can now enjoy all ShopNest features."
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 7: ResendVerificationView
# POST /api/auth/resend-verification/
# ═════════════════════════════════════════════════════════════════════════════
class ResendVerificationView(APIView):
    """
    Re-sends the verification email to the logged-in user.
    Used when the original email expired or was lost.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.email_verified:
            return error_response(
                message="Your email address is already verified.",
                status_code=400
            )

        send_verification_email(user, request)

        return success_response(
            message="Verification email sent! Please check your inbox."
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 8: AdminUserListView
# GET /api/auth/admin/users/
# ═════════════════════════════════════════════════════════════════════════════
class AdminUserListView(APIView):
    """
    Admin-only endpoint that lists all registered users.
    Used by the Admin Dashboard in the React frontend.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by('-date_joined')
        serializer = PublicUserSerializer(
            users,
            many=True,
            context={'request': request}
        )
        return success_response(
            data=serializer.data,
            message=f"{users.count()} users found."
        )


# ═════════════════════════════════════════════════════════════════════════════
# VIEW 9: AdminUserDetailView
# GET   /api/auth/admin/users/<pk>/ → view a specific user
# PATCH /api/auth/admin/users/<pk>/ → toggle active/admin status
# ═════════════════════════════════════════════════════════════════════════════
class AdminUserDetailView(APIView):
    """
    Admin-only endpoint for viewing and managing a specific user.
    """
    permission_classes = [IsAdminUser]

    def _get_user(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return error_response(message="User not found.", status_code=404)

        serializer = PublicUserSerializer(user, context={'request': request})
        return success_response(data=serializer.data)

    def patch(self, request, pk):
        """Toggle is_active or is_admin fields."""
        user = self._get_user(pk)
        if not user:
            return error_response(message="User not found.", status_code=404)

        # Only allow toggling safe fields from admin panel
        allowed_fields = ['is_active', 'is_admin']
        for field in allowed_fields:
            if field in request.data:
                setattr(user, field, request.data[field])

        user.save()
        serializer = PublicUserSerializer(user, context={'request': request})
        return success_response(
            data=serializer.data,
            message="User updated successfully."
        )
