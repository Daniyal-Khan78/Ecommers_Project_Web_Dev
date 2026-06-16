from pathlib import Path
from datetime import timedelta

# ─── Base Directory ────────────────────────────────────────────────────────────
# BASE_DIR points to: shopnest/backend/
# All other paths are built relative to this.
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ──────────────────────────────────────────────────────────────────
# SECRET_KEY is used by Django for cryptographic signing.
# IMPORTANT: Never share or commit this key in production.
SECRET_KEY = 'django-insecure-shopnest-change-this-in-production-xyz123abc456'

# DEBUG=True shows detailed error pages. Must be False in production.
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ─── Installed Applications ────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party packages
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',

    # Our custom apps
    'users',
    'products',
    'cart',
    'wishlist',
    'orders',
    'notifications',
]

# ─── Middleware ────────────────────────────────────────────────────────────────
# Middleware processes every HTTP request before it reaches our views.
# Order is critical — CorsMiddleware MUST come before CommonMiddleware.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

# ─── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# ─── Database ──────────────────────────────────────────────────────────────────
# SQLite is a file-based database — no server required.
# The database file will be created at: shopnest/backend/db.sqlite3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ─── Custom User Model ─────────────────────────────────────────────────────────
# Tell Django to use our custom User model (defined in users/models.py)
# instead of its built-in User model.
AUTH_USER_MODEL = 'users.User'

# ─── Password Validation ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internationalization ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ─── Static & Media Files ──────────────────────────────────────────────────────
STATIC_URL = '/static/'

# MEDIA files = files uploaded by users (product images, profile pictures)
# MEDIA_URL  = the URL prefix to access them in the browser
# MEDIA_ROOT = the folder on disk where they are stored
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Default Primary Key ───────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Django REST Framework Configuration ───────────────────────────────────────
REST_FRAMEWORK = {
    # ── Authentication ──────────────────────────────────────────────────────────
    # Every API request is authenticated using JWT tokens.
    # The token is read from the "Authorization: Bearer <token>" header.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    # ── Permissions ─────────────────────────────────────────────────────────────
    # By default, all endpoints require a logged-in user.
    # Individual views override this where needed (e.g., product list is public).
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),

    # ── Exception Handler ────────────────────────────────────────────────────────
    # Our custom handler converts all DRF exceptions into our standard JSON format.
    # Without this, 401/403/404 errors return DRF's own format, not ours.
    'EXCEPTION_HANDLER': 'utils.exceptions.custom_exception_handler',

    # ── Pagination ───────────────────────────────────────────────────────────────
    # All list endpoints are paginated by default.
    # Clients request pages like: GET /api/products/?page=2
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,   # 12 products per page (3 rows × 4 columns in the grid)

    # ── Throttling (Rate Limiting) ────────────────────────────────────────────────
    # Limits how many requests a single user/IP can make.
    # Protects against brute-force login attempts and API abuse.
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',   # For unauthenticated users
        'rest_framework.throttling.UserRateThrottle',   # For authenticated users
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '200/day',    # Unauthenticated: 200 requests per day
        'user': '2000/day',   # Authenticated:   2000 requests per day
    },

    # ── Renderer ─────────────────────────────────────────────────────────────────
    # Only output JSON — no HTML browsable API in production.
    # During development you can add BrowsableAPIRenderer for a nice UI.
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Remove in production
    ],
}

# ─── JWT (JSON Web Token) Configuration ────────────────────────────────────────
SIMPLE_JWT = {
    # Access token: short-lived (60 min). Used in every API request.
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    # Refresh token: long-lived (7 days). Used only to get new access tokens.
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    # Issue a new refresh token each time the old one is used
    'ROTATE_REFRESH_TOKENS': True,
    # Add old refresh tokens to blacklist so they can't be reused
    'BLACKLIST_AFTER_ROTATION': True,
    # Cryptographic algorithm for signing tokens
    'ALGORITHM': 'HS256',
    # Format of the Authorization header: "Bearer <token>"
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ─── CORS Configuration ────────────────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) allows our React app running on port 3000
# to make requests to our Django API running on port 8000.
# Without this, the browser would block all requests between the two servers.
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
CORS_ALLOW_CREDENTIALS = True

# ─── Email Configuration ───────────────────────────────────────────────────────
# During development, emails are printed to the terminal console
# so you can see them without needing a real mail server.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'ShopNest <noreply@shopnest.com>'

# ─── Stripe Configuration ──────────────────────────────────────────────────────
# Stripe accepts ALL major card networks: Visa, Mastercard, Amex, Discover, etc.
# One integration — all cards.
#
# Get your FREE test keys from: https://dashboard.stripe.com/register
# Developers → API keys → copy pk_test_... and sk_test_...
#
# Test cards (use these in development — real cards are NEVER needed for testing):
#   Visa success:        4242 4242 4242 4242  exp: any future date  cvv: any 3 digits
#   Mastercard success:  5555 5555 5555 4444  exp: any future date  cvv: any 3 digits
#   Amex success:        3782 822463 10005    exp: any future date  cvv: any 4 digits
#   Visa 3D Secure:      4000 0027 6000 3184  (requires authentication step)
#   Card declined:       4000 0000 0000 0002  (simulates decline)
#   Insufficient funds:  4000 0000 0000 9995  (simulates insufficient funds)
STRIPE_SECRET_KEY      = 'sk_test_your_stripe_secret_key_here'
STRIPE_PUBLISHABLE_KEY = 'pk_test_your_stripe_publishable_key_here'

# Webhook signing secret — get this by running:
#   stripe listen --forward-to localhost:8000/api/payments/webhook/
# in the Stripe CLI. Starts with whsec_...
STRIPE_WEBHOOK_SECRET  = 'whsec_your_webhook_secret_here'

# Supported payment methods exposed to the frontend
STRIPE_PAYMENT_METHODS = ['card']   # 'card' covers Visa, Mastercard, Amex, etc.
