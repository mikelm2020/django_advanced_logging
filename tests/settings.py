"""
Django settings para tests de django-advanced-logging.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'test-secret-key-for-django-advanced-logging'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django_advanced_logging',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Deshabilitar logging por defecto de Django para tests
LOGGING_CONFIG = None

# Configuración para django-advanced-logging (nuestra app)
# Esta será leída por DjangoAdvancedLoggingConfig.ready()
ADVANCED_LOGGING_CONFIG = {
    'name': 'test_django_app',
    'level': 'DEBUG',
    'environment': 'development',
    'console_output': False,  # No queremos output en tests
    'file_output': False,
}

USE_TZ = True
