import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
from csp.constants import NONCE, SELF

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Security: Debug mode toggled via environment
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

# Security: Secret Key from environment
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-sitewright-dev-only-secret-key-replace-in-production'  # nosec B105
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY environment variable must be set when DEBUG is False.")

# Security: Django Admin URL from environment
DJANGO_ADMIN_URL = os.environ.get('DJANGO_ADMIN_URL')
if not DJANGO_ADMIN_URL or not DJANGO_ADMIN_URL.strip():
    if DEBUG:
        DJANGO_ADMIN_URL = 'admin/'
    else:
        raise ImproperlyConfigured("DJANGO_ADMIN_URL environment variable must be set when DEBUG is False.")
else:
    DJANGO_ADMIN_URL = DJANGO_ADMIN_URL.strip()

# Security: Allowed hosts parsed safely
raw_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost')
if raw_hosts.strip() == '*':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [h.strip() for h in raw_hosts.split(',') if h.strip()]

# Render cloud deployment auto-detection:
IS_RENDER = os.environ.get('RENDER', '').lower() in ('true', '1')
render_external_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_external_hostname and render_external_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_external_hostname)

# Trusted proxy count for client IP extraction (Render uses 1 proxy layer)
try:
    default_proxy_count = '1' if IS_RENDER else '0'
    TRUSTED_PROXY_COUNT = int(os.environ.get('TRUSTED_PROXY_COUNT', default_proxy_count))
except ValueError:
    TRUSTED_PROXY_COUNT = 1 if IS_RENDER else 0

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'csp',
    'axes',
    'core.apps.CoreConfig',
]

AUTHENTICATION_BACKENDS = [
    'core.backends.SitewrightAxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'sitewright.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.contact_email',
                'csp.context_processors.nonce',
            ],
        },
    },
]

WSGI_APPLICATION = 'sitewright.wsgi.application'

# Database Configuration with Automatic Fallback (PostgreSQL -> SQLite)
def get_database_config():
    """
    Auto-detects database availability with seamless fallback:
    - Primary: PostgreSQL (if driver installed, credentials configured, and host reachable).
    - Fallback: SQLite (if PostgreSQL is not installed, not configured, or unavailable).
    """
    sqlite_config = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

    # 1. Check if a PostgreSQL driver is installed (psycopg 3 or psycopg2)
    driver = None
    try:
        import psycopg  # noqa: F401
        driver = 'psycopg'
    except ImportError:
        try:
            import psycopg2  # noqa: F401
            driver = 'psycopg2'
        except ImportError:
            driver = None

    if not driver:
        return sqlite_config

    # 2. Check if PostgreSQL configuration is provided via environment
    db_url = os.environ.get('DATABASE_URL', '').strip()
    postgres_config = None
    conn_max_age = int(os.environ.get('DJANGO_DB_CONN_MAX_AGE', '600'))

    if db_url and (db_url.startswith('postgres://') or db_url.startswith('postgresql://')):
        try:
            from urllib.parse import urlparse, unquote, parse_qs
            parsed = urlparse(db_url)
            query_params = parse_qs(parsed.query)
            options = {'connect_timeout': 5}
            if 'sslmode' in query_params:
                options['sslmode'] = query_params['sslmode'][0]

            postgres_config = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': unquote(parsed.path.lstrip('/')),
                'USER': unquote(parsed.username or ''),
                'PASSWORD': unquote(parsed.password or ''),
                'HOST': parsed.hostname or 'localhost',
                'PORT': str(parsed.port or 5432),
                'CONN_MAX_AGE': conn_max_age,
                'CONN_HEALTH_CHECKS': True,
                'OPTIONS': options,
            }
        except Exception:
            postgres_config = None
    else:
        pg_db = os.environ.get('POSTGRES_DB') or os.environ.get('DB_NAME') or os.environ.get('DJANGO_DB_NAME')
        if pg_db:
            postgres_config = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': pg_db,
                'USER': os.environ.get('POSTGRES_USER') or os.environ.get('DB_USER') or os.environ.get('DJANGO_DB_USER') or 'postgres',
                'PASSWORD': os.environ.get('POSTGRES_PASSWORD') or os.environ.get('DB_PASSWORD') or os.environ.get('DJANGO_DB_PASSWORD') or '',
                'HOST': os.environ.get('POSTGRES_HOST') or os.environ.get('DB_HOST') or os.environ.get('DJANGO_DB_HOST') or 'localhost',
                'PORT': str(os.environ.get('POSTGRES_PORT') or os.environ.get('DB_PORT') or os.environ.get('DJANGO_DB_PORT') or '5432'),
                'CONN_MAX_AGE': conn_max_age,
                'CONN_HEALTH_CHECKS': True,
                'OPTIONS': {'connect_timeout': 5},
            }

    if not postgres_config or not postgres_config.get('NAME'):
        return sqlite_config

    # 3. Test PostgreSQL availability (quick connectivity probe with 2s timeout)
    try:
        probe_kwargs = {
            'dbname': postgres_config['NAME'],
            'user': postgres_config['USER'],
            'password': postgres_config['PASSWORD'],
            'host': postgres_config['HOST'],
            'port': postgres_config['PORT'],
            'connect_timeout': 2,
        }
        if 'sslmode' in postgres_config.get('OPTIONS', {}):
            probe_kwargs['sslmode'] = postgres_config['OPTIONS']['sslmode']

        if driver == 'psycopg':
            import psycopg
            conn = psycopg.connect(**probe_kwargs)
            conn.close()
        elif driver == 'psycopg2':
            import psycopg2
            conn = psycopg2.connect(**probe_kwargs)
            conn.close()

        # PostgreSQL is reachable and verified
        return postgres_config
    except Exception as exc:
        import logging
        logging.getLogger('sitewright').info(
            "PostgreSQL database '%s' at %s:%s is unavailable (%s). Falling back to SQLite.",
            postgres_config['NAME'],
            postgres_config['HOST'],
            postgres_config['PORT'],
            exc,
        )
        return sqlite_config


DATABASES = {
    'default': get_database_config()
}

# Cache configuration:
# LocMemCache is per-process in memory and not suitable for multi-worker production.
# Set REDIS_URL in production environments for shared caching and rate limiting across workers.
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    try:
        import redis  # noqa: F401
    except ImportError as exc:
        raise ImproperlyConfigured("REDIS_URL is configured but the 'redis' package is not installed.") from exc
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'sitewright-security-cache',
        }
    }

# Strong Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Contact, Profile & Conversion Settings
WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '')
BOOKING_URL = os.environ.get('BOOKING_URL', '')
DEVELOPER_NAME = os.environ.get('DEVELOPER_NAME', 'Shlok Suthar')
DEVELOPER_CITY = os.environ.get('DEVELOPER_CITY', 'Ahmedabad, India')
GITHUB_URL = os.environ.get('GITHUB_URL', 'https://github.com/shloksuthar0307-sketch')
LINKEDIN_URL = os.environ.get('LINKEDIN_URL', 'https://linkedin.com')
PLAUSIBLE_DOMAIN = os.environ.get('PLAUSIBLE_DOMAIN', '')

# Production Static & Media Storage Configuration
USE_S3_STORAGE = os.environ.get('USE_S3_STORAGE', 'False').lower() in ('true', '1', 'yes')

if USE_S3_STORAGE:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# WhiteNoise Production Settings
WHITENOISE_MANIFEST_STRICT = os.environ.get('WHITENOISE_MANIFEST_STRICT', 'False').lower() in ('true', '1', 'yes')
WHITENOISE_MAX_AGE = int(os.environ.get('WHITENOISE_MAX_AGE', '31536000'))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session Cookie Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Production Security Headers & Reverse Proxy Settings
USE_PROXY_SSL_HEADER = os.environ.get(
    'USE_PROXY_SSL_HEADER',
    'True' if IS_RENDER else 'False'
).lower() in ('true', '1', 'yes')

ssl_redirect_env = os.environ.get('DJANGO_SSL_REDIRECT')
if ssl_redirect_env is not None:
    SECURE_SSL_REDIRECT = ssl_redirect_env.lower() in ('true', '1', 'yes')
else:
    SECURE_SSL_REDIRECT = not DEBUG

if not DEBUG:
    if USE_PROXY_SSL_HEADER:
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
else:
    # Standard framing protection in development
    X_FRAME_OPTIONS = 'SAMEORIGIN'

# Content-Security-Policy (CSP) Configuration
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [SELF],
        "script-src": [SELF, "https://plausible.io", "https://chatzy-kb-store.s3.amazonaws.com", NONCE],
        "style-src": [SELF, "https://fonts.googleapis.com", "https://chatzy-kb-store.s3.amazonaws.com", NONCE],
        "font-src": [SELF, "https://fonts.gstatic.com", "https://chatzy-kb-store.s3.amazonaws.com"],
        "img-src": [SELF, "data:", "https://chatzy-kb-store.s3.amazonaws.com", "https:"],
        "connect-src": [SELF, "https://plausible.io", "https://chatzy-kb-store.s3.amazonaws.com", "https:"],
        "frame-src": [SELF, "https:"],
    }
}

# Django-Axes Brute-Force Defense Configuration
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=5)
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_CLIENT_IP_CALLABLE = 'core.views.get_client_ip'
AXES_ONLY_ADMIN_SITE = True
AXES_HANDLER = 'core.axes_handler.SitewrightAxesHandler'

raw_csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if raw_csrf_origins:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in raw_csrf_origins.split(',') if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []

if render_external_hostname:
    render_origin = f"https://{render_external_hostname}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

# Email Notification Settings
EMAIL_BACKEND = os.environ.get('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
ADMIN_NOTIFICATION_EMAIL = os.environ.get('ADMIN_NOTIFICATION_EMAIL', 'admin@sitewright.ai')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@sitewright.ai')

# Authentication URLs
LOGIN_URL = 'core:admin_login'
LOGIN_REDIRECT_URL = 'core:admin_dashboard'
LOGOUT_REDIRECT_URL = 'core:admin_login'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'sitewright': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
