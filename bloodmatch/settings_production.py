"""
Production settings for BloodMatch backend.
Import base settings and override with production-safe values.
"""

import os
import dj_database_url
from .settings import *  # noqa: F401,F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Secret key from environment variable
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-change-me')

# Only allow specific hosts
# Render gives you a URL like bloodmatch-backend.onrender.com
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
]

# Add the Render domain from environment variable if set
render_host = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if render_host:
    ALLOWED_HOSTS.append(render_host)


# Database - read from DATABASE_URL (Render injects this for PostgreSQL)
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600,
        ssl_require=True
    )
}


# CORS settings - production only
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]

# Add frontend URL from environment if set
frontend_url = os.getenv('FRONTEND_URL')
if frontend_url:
    CORS_ALLOWED_ORIGINS.append(frontend_url)


# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# If using HTTPS (recommended for production)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
