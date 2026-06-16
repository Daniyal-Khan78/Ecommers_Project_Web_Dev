from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 1: UserRegistrationSerializer
# Used by: POST /api/auth/register/
# ─────────────────────────────────────────────────────────────────────────────
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Validates and creates a new user account.

    ModelSerializer automatically generates fields from the User model.
    We declare extra fields here that aren't on the model (password2)
    or that need special handling (password — write-only, never returned).
    """

    # write_only=True means this field is accepted in input but NEVER
    # included in the serialized output. Passwords must never be returned
    # in API responses, even in hashed form.
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}   # Tells Browsable API to render as a password input
    )

    # Confirmation field — not on the model, only used for validation.
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        # Fields the client must/can send when registering.
        fields = ['username', 'email', 'password', 'password2',
                  'first_name', 'last_name', 'phone']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name':  {'required': True},
            'email':      {'required': True},
        }

    def validate_email(self, value):
        """
        Field-level validator for the email field.
        Called automatically by serializer.is_valid() before validate().

        We manually check uniqueness here because the error message from
        Django's default unique constraint is not user-friendly.
        """
        # .lower() normalises the email so 'Test@Email.com' == 'test@email.com'
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError(
                "An account with this email address already exists."
            )
        return value.lower()

    def validate_username(self, value):
        """Ensure username doesn't contain spaces and is lowercase."""
        if ' ' in value:
            raise serializers.ValidationError("Username cannot contain spaces.")
        return value.lower()

    def validate_password(self, value):
        """
        Run Django's built-in password validators (configured in settings.py).
        These check for: minimum length, common passwords, all-numeric passwords, etc.
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """
        Cross-field validator — runs AFTER all field-level validators pass.
        Used here to confirm password and password2 match.

        'attrs' is a dict of all the validated field values.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "The two password fields do not match."}
            )
        return attrs

    def create(self, validated_data):
        """
        Called by serializer.save() after validation passes.
        Creates the User with a properly HASHED password.

        We must use create_user() (not User.objects.create()) because:
          - create_user() calls set_password() which hashes the password
          - User.objects.create() stores the password in PLAIN TEXT (a security disaster)
        """
        # Remove password2 — it's only for validation, not stored anywhere
        validated_data.pop('password2')
        password = validated_data.pop('password')

        # create_user() creates the user AND hashes the password
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 2: UserLoginSerializer
# Used by: POST /api/auth/login/
# ─────────────────────────────────────────────────────────────────────────────
class UserLoginSerializer(serializers.Serializer):
    """
    Validates login credentials and returns the authenticated user.

    We use the base Serializer (not ModelSerializer) because we're not
    creating or reading a model instance — we're just validating credentials.

    We support login by BOTH email and username for flexibility.
    """

    # Accept email as the primary login identifier
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email    = attrs.get('email', '').lower()
        password = attrs.get('password', '')

        # Step 1: Find the user by email (our preferred login method)
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "No account found with this email address."}
            )

        # Step 2: Django's authenticate() verifies the password against the hash.
        # Returns the User object if credentials are valid, None otherwise.
        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError(
                {"password": "Incorrect password. Please try again."}
            )

        # Step 3: Check account is active (not banned/suspended)
        if not user.is_active:
            raise serializers.ValidationError(
                {"email": "This account has been deactivated. Please contact support."}
            )

        # Attach the user object to attrs so the view can access it
        attrs['user'] = user
        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 3: UserProfileSerializer
# Used by: GET /api/auth/profile/  and  PUT/PATCH /api/auth/profile/update/
# ─────────────────────────────────────────────────────────────────────────────
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Read/write serializer for a user's profile.

    For GET requests: serializes user data to JSON (output).
    For PUT/PATCH requests: validates and updates user data (input).
    """

    # SerializerMethodField is a read-only field whose value is computed
    # by the method named 'get_<field_name>' on this class.
    # We use it for profile_image to return a full URL instead of just the path.
    profile_image_url = serializers.SerializerMethodField()
    is_admin          = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'address', 'profile_image', 'profile_image_url',
            'is_admin', 'email_verified', 'date_joined'
        ]
        read_only_fields = [
            'id', 'email', 'username', 'is_admin',
            'email_verified', 'date_joined', 'profile_image_url'
        ]
        extra_kwargs = {
            # profile_image is write-only in the sense that we don't want
            # the raw file path returned — we use profile_image_url instead.
            'profile_image': {'write_only': True, 'required': False},
        }

    def get_profile_image_url(self, obj):
        request = self.context.get('request')
        if obj.profile_image and request:
            return request.build_absolute_uri(obj.profile_image.url)
        return None

    def get_is_admin(self, obj):
        # Treat Django superusers and staff as admin too,
        # so accounts created via createsuperuser work correctly.
        return obj.is_admin or obj.is_staff or obj.is_superuser


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 4: ChangePasswordSerializer
# Used by: POST /api/auth/change-password/
# ─────────────────────────────────────────────────────────────────────────────
class ChangePasswordSerializer(serializers.Serializer):
    """
    Validates and processes a password change request.
    Requires the user to confirm their current password first (security).
    """

    old_password     = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password     = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_new_password(self, value):
        """Run Django's built-in password validators on the new password."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {"confirm_password": "New passwords do not match."}
            )
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from the current password."}
            )
        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# SERIALIZER 5: PublicUserSerializer
# Used by: Admin endpoints that list users (read-only, safe subset of fields)
# ─────────────────────────────────────────────────────────────────────────────
class PublicUserSerializer(serializers.ModelSerializer):
    """
    A minimal, read-only serializer for displaying user info to admins.
    Does NOT include password or sensitive internal fields.
    """
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'is_admin', 'is_active', 'email_verified',
            'date_joined', 'profile_image_url'
        ]
        read_only_fields = fields

    def get_profile_image_url(self, obj):
        request = self.context.get('request')
        if obj.profile_image and request:
            return request.build_absolute_uri(obj.profile_image.url)
        return None
