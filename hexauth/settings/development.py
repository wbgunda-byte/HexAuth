"""
Development settings for HexAUTH project.
"""
from .base import *

DEBUG = True

# Database
DATABASES['default'].update({
    'NAME': 'hexauth_dev',
})

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug toolbar
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

# Disable security features in development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0