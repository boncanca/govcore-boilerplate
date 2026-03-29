import os
import runpy
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = []

LOCAL_APPS = [
    "apps.users",
    "core.identity",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls.public"
WSGI_APPLICATION = "config.wsgi.application"

db_url = urlparse(os.environ.get("DATABASE_URL", "postgresql://localhost:5432/postgres"))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": db_url.path.lstrip("/") or "postgres",
        "USER": db_url.username or "postgres",
        "PASSWORD": db_url.password or "",
        "HOST": db_url.hostname or "localhost",
        "PORT": str(db_url.port or "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"connect_timeout": 10},
    }
}

REST_FRAMEWORK = {}
SPECTACULAR_SETTINGS = {}

CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Accra"
USE_I18N = True
USE_TZ = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:4200").split(",")

# ============================================================================
# Identity & Authentication Configuration
# ============================================================================

AUTH_USER_MODEL = "users.User"

# MFA configuration
MFA_REQUIRED_BY_DEFAULT = True
MFA_TOTP_WINDOW = 1  # ±30 seconds for TOTP validation

# Authentication backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# Session configuration
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True

# Optional generated feature settings for template consumers.
FEATURE_SETTINGS_FILE = BASE_DIR / "config" / "settings" / "features.py"
if FEATURE_SETTINGS_FILE.exists():
    feature_state = runpy.run_path(
        str(FEATURE_SETTINGS_FILE),
        init_globals=dict(globals()),
    )
    for setting_name, setting_value in feature_state.items():
        if setting_name.isupper():
            globals()[setting_name] = setting_value
