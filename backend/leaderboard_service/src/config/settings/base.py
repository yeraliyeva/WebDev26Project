from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default='django-insecure-%rrkt5*7i%js+o9)annv=v3g83$4^k(r_*2b@y-l2^duu0&rn0')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

FORCE_SCRIPT_NAME = config("FORCE_SCRIPT_NAME", default="") or None

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")


# Application definition

INSTALLED_APPS = [
    "django_prometheus",
    "django.contrib.admin",
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'channels',
    'leaderboard',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'config.middleware.ForwardedPrefixMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": config("DJANGO_DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": config("DJANGO_DB_NAME", default=str(BASE_DIR / "db.sqlite3")),
        "USER": config("DJANGO_DB_USER", default=""),
        "PASSWORD": config("DJANGO_DB_PASSWORD", default=""),
        "HOST": config("DJANGO_DB_HOST", default=""),
        "PORT": config("DJANGO_DB_PORT", default=""),
    }
}

if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": config("DJANGO_DB_NAME", default=str(BASE_DIR / "db.sqlite3")),
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

# Static files (CSS, JavaScript, Images) & S3
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="")
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_FILE_OVERWRITE = False
AWS_S3_URL_PROTOCOL = "http:"

if AWS_STORAGE_BUCKET_NAME and AWS_S3_ENDPOINT_URL:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_S3_CUSTOM_DOMAIN = f"localhost:9000/{AWS_STORAGE_BUCKET_NAME}"
    STATIC_URL = f"http://{AWS_S3_CUSTOM_DOMAIN}/typecat-static/"
else:
    STATIC_URL = "typecat-static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "leaderboard.presentation.exception_handler.custom_exception_handler",
}

# Redis
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

# Kafka
KAFKA_BOOTSTRAP_SERVERS = config("KAFKA_BOOTSTRAP_SERVERS", default="localhost:9092")
KAFKA_GROUP_ID = config("KAFKA_GROUP_ID", default="leaderboard-service")
KAFKA_TOPIC_SUBMIT_REWARDED = config("KAFKA_TOPIC_SUBMIT_REWARDED", default="submit.rewarded")

# Leaderboard
LEADERBOARD_TOP_N = config("LEADERBOARD_TOP_N", default=10, cast=int)

# ── WebSocket / Channels ──────────────────────────────────────────────────
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [config("REDIS_CHANNEL_URL", default="redis://redis:6379/1")]},
    }
}

# ── Observability ────────────────────────────────────────────────────────────
OTLP_ENDPOINT = config("OTLP_ENDPOINT", default="http://tempo:4317")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(service)s %(env)s %(message)s",
        }
    },
    "filters": {
        "service_context": {"()": "config.logging.ServiceContextFilter", "service_name": "leaderboard_service"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["service_context"],
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}


# S3 / Storage — only enabled when AWS_STORAGE_BUCKET_NAME is set
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="")
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_FILE_OVERWRITE = False
AWS_S3_URL_PROTOCOL = "http"

if AWS_STORAGE_BUCKET_NAME and AWS_S3_ENDPOINT_URL:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_S3_URL_PROTOCOL}://localhost:9000/{AWS_STORAGE_BUCKET_NAME}/"
    # Keep staticfiles local in dev to avoid brittle collectstatic-on-S3 behavior.
    STATIC_URL = AWS_S3_CUSTOM_DOMAIN
else:
    STATIC_URL = "typecat-static/"