"""
Production settings for BloodMatch backend.
Import base settings and override with production-safe values.
"""

from .settings import *  # noqa: F401,F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Only allow specific hosts
ALLOWED_HOSTS = [
    'yourdomain.com',
    'www.yourdomain.com',
    'api.yourdomain.com',
    # Add your production domain here
]

# CORS settings - production only
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
CORS_ALLOW_CREDENTIALS = True

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# If using HTTPS (recommended for production)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
