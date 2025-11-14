"""
Ejemplo de configuración de Django settings.py para django-advanced-logging.

Copia y pega estas configuraciones en tu settings.py
"""

import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# INSTALACIÓN: Agregar django_advanced_logging a INSTALLED_APPS
# ============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # django-advanced-logging (agregar antes de tus apps)
    'django_advanced_logging',
    
    # Tus aplicaciones
    'myapp',
]

# ============================================================================
# MIDDLEWARE: Agregar LoggingMiddleware (Opcional pero recomendado)
# ============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Logging de todas las peticiones HTTP
    'django_advanced_logging.django.middleware.LoggingMiddleware',
    
    # Logging de integraciones externas (ERPs, webhooks, Magento, etc.)
    'django_advanced_logging.django.integrations_middleware.ExternalIntegrationLoggingMiddleware',
]

# ============================================================================
# CONFIGURACIÓN DE DJANGO-ADVANCED-LOGGING
# ============================================================================

# Opción 1: Configuración básica (usa variables de entorno)
# La app leerá automáticamente: LOG_NAME, LOG_LEVEL, LOG_ENVIRONMENT, etc.

# Opción 2: Configuración manual en settings.py
LOGGING_CONFIG = {
    'name': os.getenv('LOG_NAME', 'django_app'),
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'environment': os.getenv('LOG_ENVIRONMENT', 'development' if DEBUG else 'production'),
    'log_dir': BASE_DIR / 'logs',
    'console_output': True,
    'file_output': True,
    'rotate_logs': True,
    'max_bytes': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
    'json_format': not DEBUG,  # JSON en producción, texto en desarrollo
    'mask_sensitive': True,  # Enmascarar passwords, tokens, etc.
}

# ============================================================================
# CONFIGURACIÓN DE POSTGRESQL (Opcional)
# ============================================================================

# Habilitar solo si POSTGRES_ENABLED=true
if os.getenv('POSTGRES_ENABLED', 'false').lower() == 'true':
    LOGGING_CONFIG['postgres_enabled'] = True
    LOGGING_CONFIG['postgres_config'] = {
        'host': os.getenv('# LOG_DB_HOST (auto desde DATABASES)', 'localhost'),
        'port': int(os.getenv('# LOG_DB_PORT (auto desde DATABASES)', '5432')),
        'database': os.getenv('# LOG_DB_NAME (auto desde DATABASES)', 'django_db'),
        'user': os.getenv('# LOG_DB_USER (auto desde DATABASES)', 'postgres'),
        'password': os.getenv('# LOG_DB_PASSWORD (auto desde DATABASES)', ''),
        'table_name': os.getenv('LOG_DB_TABLE', 'application_logs'),
        'buffer_size': int(os.getenv('LOG_BUFFER_SIZE', '1000')),
        'batch_size': int(os.getenv('LOG_BATCH_SIZE', '10')),
        'flush_interval': float(os.getenv('LOG_FLUSH_INTERVAL', '5.0')),
    }

# ============================================================================
# CONFIGURACIÓN DE RUTAS DE INTEGRACIÓN (Opcional)
# ============================================================================

# Personalizar rutas que el ExternalIntegrationLoggingMiddleware monitoreará
INTEGRATION_MONITORED_PATHS = [
    '/api/erp/',
    '/api/integrations/',
    '/api/external/',
    '/webhook/',
    '/api/payment/',
    '/api/shipping/',
    '/api/magento/',
    '/api/custom/',  # Agregar tus rutas personalizadas
]

# Mapeo de rutas a tipos de integración
INTEGRATION_TYPES = {
    '/api/erp/': 'erp',
    '/api/magento/': 'magento',
    '/api/custom/': 'custom_integration',
    # ...
}

# ============================================================================
# EJEMPLO DE USO EN VIEWS
# ============================================================================

"""
# En tus views.py:

from django_advanced_logging import get_logger

logger = get_logger(__name__)

def my_view(request):
    logger.info(
        f"Usuario {request.user} accedió a la vista",
        extra={
            'extra_fields': {
                'user_id': request.user.id,
                'path': request.path,
                'method': request.method,
                'ip': request.META.get('REMOTE_ADDR'),
            }
        }
    )
    
    try:
        # Tu lógica
        return Response({"status": "success"})
    except Exception as e:
        logger.error(
            f"Error en vista: {str(e)}",
            exc_info=True,
            extra={
                'extra_fields': {
                    'user_id': request.user.id,
                    'view': 'my_view',
                }
            }
        )
        raise
"""

# ============================================================================
# MIGRACIONES
# ============================================================================

"""
Después de configurar, ejecutar:

# 1. Crear la tabla de logs en PostgreSQL
python manage.py migrate

# 2. (Opcional) Comando de prueba
python manage.py test_logging

# El paquete creará automáticamente la tabla 'application_logs'
"""

# ============================================================================
# DESHABILITAR EL LOGGING POR DEFECTO DE DJANGO (Opcional)
# ============================================================================

# Si quieres que SOLO django-advanced-logging maneje los logs:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {},
    'loggers': {},
}

# O puedes mantener ambos sistemas de logging
