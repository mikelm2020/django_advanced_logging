"""
Configuración para desarrollo local.
"""

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'django_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# django-advanced-logging para LOCAL
LOGGING_CONFIG.update({
    'level': 'DEBUG',
    'environment': 'development',
    'console_output': True,
    'file_output': False,  # No necesitamos archivos en local
    'json_format': False,  # Texto legible para debugging
    'postgres_enabled': os.getenv('POSTGRES_ENABLED', 'true').lower() == 'true',
})

# Email backend para desarrollo
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug toolbar (opcional)
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']
