"""
Production settings for BloodMatch backend.
Import base settings and override with production-safe values.
"""

import os
import dj_database_url
from .settings import *  # noqa: F401,F403

# SECURITY WARNING: don\'t run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Secret key from environment variable
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-change-me')

# Only allow specific hosts
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
]

# Add hosts from environment variable (comma-separated)
allowed_hosts_env = os.getenv('ALLOWED_HOSTS', '')
if allowed_hosts_env:
    for host in allowed_hosts_env.split(','):
        host = host.strip()
        if host and host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)

# Add Render domain from environment variable if set
render_host = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if render_host and render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_host)


# Database - read from DATABASE_URL (Render and Docker both use this)
database_url = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')

# SSL require only if not in Docker (Docker containers talk over internal network, no SSL needed)
ssl_require = os.getenv('DATABASE_SSL', 'True').lower() == 'true'

DATABASES = {
    'default': dj_database_url.config(
        default=database_url,
        conn_max_age=600,
        ssl_require=ssl_require
    )
}


# CORS settings - production only
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = []

# Add frontend URLs from environment variable (comma-separated)
cors_origins_env = os.getenv('CORS_ALLOWED_ORIGINS', '')
if cors_origins_env:
    for origin in cors_origins_env.split(','):
        origin = origin.strip()
        if origin and origin not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(origin)


# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# If using HTTPS (recommended for production)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
