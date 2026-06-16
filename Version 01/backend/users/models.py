from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's built-in AbstractUser.

    AbstractUser already provides:
      - username, email, password (hashed automatically)
      - first_name, last_name
      - is_staff, is_active, is_superuser
      - date_joined, last_login
      - All authentication methods (check_password, etc.)

    We add extra fields below for our e-commerce needs.
    """

    # Override email to make it UNIQUE and REQUIRED.
    # Django's default AbstractUser allows duplicate emails.
    # We want email to be the primary way users identify themselves.
    email = models.EmailField(unique=True)

    # Phone number for order contact / delivery updates.
    # blank=True means this field is optional (not required in forms).
    phone = models.CharField(max_length=20, blank=True)

    # Default shipping address. Can be overridden at checkout.
    # TextField has no max length limit (unlike CharField).
    address = models.TextField(blank=True)

    # Profile picture. Uploaded files go into the media/profiles/ folder.
    # blank=True and null=True both needed for optional image fields:
    #   null=True  → the database column can store NULL
    #   blank=True → the form field is not required
    profile_image = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    # Distinguishes admin users from regular customers.
    # is_staff (from AbstractUser) controls Django admin panel access.
    # is_admin controls access to OUR custom admin dashboard in React.
    is_admin = models.BooleanField(default=False)

    # Tracks whether the user has verified their email address.
    # New users default to False. Set to True after email link is clicked.
    email_verified = models.BooleanField(default=False)

    # The __str__ method controls what appears when this object is
    # displayed as text (e.g., in the Django admin panel or print()).
    def __str__(self):
        return f"{self.username} ({self.email})"

    class Meta:
        # Controls the order records appear in querysets and admin panel.
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
