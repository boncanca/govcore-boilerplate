from .base import *

DEBUG = False
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
