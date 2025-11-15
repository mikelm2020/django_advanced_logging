"""
Ejemplo de configuración de Django settings.py para django-advanced-logging.

Copia y pega estas configuraciones en tu settings.py según tu ambiente.
"""

import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# PASO 1: Agregar django_advanced_logging a INSTALLED_APPS
# ============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # django-advanced-logging - AGREGAR AQUÍ
    'django_advanced_logging',

    # Tus aplicaciones
    'myapp',
]

# ============================================================================
# PASO 2: Configurar la base de datos PostgreSQL (REQUERIDO)
# ============================================================================

# django-advanced-logging usa automáticamente la configuración de DATABASES['default']
# No necesitas configurar la conexión por separado

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'django_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),  # o 'db' en Docker
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# ============================================================================
# PASO 3: Configurar LOGGING_CONFIG
# ============================================================================

# --- OPCIÓN A: Configuración Básica (Mínima) ---

LOGGING_CONFIG = {
    'version': 1,
    'name': 'mi_proyecto',
    'environment': 'development',  # 'development', 'staging' o 'production'
    'log_level': 'INFO',

    # Consola
    'console': {
        'enabled': True,
        'colored': True,  # Colores ANSI en desarrollo
    },

    # PostgreSQL - Auto-configurado desde DATABASES['default']
    'postgres': {
        'enabled': True,
    },
}

# --- OPCIÓN B: Configuración Completa ---

LOGGING_CONFIG = {
    'version': 1,
    'name': os.getenv('PROJECT_NAME', 'mi_proyecto'),
    'environment': os.getenv('ENVIRONMENT', 'development'),
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),

    # Configuración de consola
    'console': {
        'enabled': True,
        'colored': not os.getenv('DOCKER', False),  # Sin colores en Docker
        'format': '[%(levelname)s] %(name)s - %(message)s',
    },

    # Configuración de archivo (opcional)
    'file': {
        'enabled': True,
        'path': os.getenv('LOG_FILE_PATH', '/var/log/django/app.log'),
        'max_bytes': 10485760,  # 10 MB
        'backup_count': 5,
        'format': '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    },

    # Configuración de PostgreSQL
    'postgres': {
        'enabled': True,
        'table_name': 'application_logs',
        'buffer_size': 1000,
        'batch_size': 100,
        'flush_interval': 5.0,
    },

    # Filtros
    'filters': {
        'sensitive_data': True,  # Filtra passwords, tokens, API keys
        'environment': True,     # Agrega info de ambiente a cada log
    },

    # Formatters
    'formatters': {
        'console': 'colored',  # 'colored' o 'json'
        'file': 'standard',    # 'standard' o 'json'
        'postgres': 'json',    # Siempre 'json' para postgres
    },
}

# --- OPCIÓN C: Configuración por Ambiente (Recomendado) ---

# Si usas settings separados por ambiente (settings/local.py, settings/production.py):
# Ver examples/settings/ para ejemplos completos

if os.getenv('ENVIRONMENT') == 'development':
    LOGGING_CONFIG = {
        'version': 1,
        'name': 'mi_proyecto',
        'environment': 'development',
        'log_level': 'DEBUG',  # Debug en desarrollo
        'console': {
            'enabled': True,
            'colored': True,
        },
        'postgres': {
            'enabled': True,
        },
    }

elif os.getenv('ENVIRONMENT') == 'staging':
    LOGGING_CONFIG = {
        'version': 1,
        'name': 'mi_proyecto',
        'environment': 'staging',
        'log_level': 'INFO',
        'console': {
            'enabled': True,
            'colored': False,
        },
        'file': {
            'enabled': True,
            'path': '/var/log/django/app.log',
        },
        'postgres': {
            'enabled': True,
            'batch_size': 200,
        },
    }

elif os.getenv('ENVIRONMENT') == 'production':
    LOGGING_CONFIG = {
        'version': 1,
        'name': 'mi_proyecto',
        'environment': 'production',
        'log_level': 'WARNING',  # Solo WARNING+ en producción
        'console': {
            'enabled': False,  # Sin consola en producción
        },
        'file': {
            'enabled': True,
            'path': '/var/log/django/app.log',
            'max_bytes': 52428800,  # 50 MB
            'backup_count': 10,
        },
        'postgres': {
            'enabled': True,
            'buffer_size': 5000,
            'batch_size': 500,
            'flush_interval': 10.0,
        },
        'filters': {
            'sensitive_data': True,  # CRÍTICO en producción
            'environment': True,
        },
    }

# ============================================================================
# PASO 4: Agregar Middleware (Opcional pero Recomendado)
# ============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Logging de todas las requests HTTP
    # Loguea automáticamente: método, path, user, IP, status, duración
    'django_advanced_logging.django.middleware.LoggingMiddleware',

    # Logging de integraciones externas (opcional)
    # Útil para APIs externas, ERPs, webhooks, etc.
    # 'django_advanced_logging.django.integrations_middleware.ExternalIntegrationLoggingMiddleware',
]

# ============================================================================
# Configuración del Middleware de Integraciones (si lo usas)
# ============================================================================

# Rutas que se consideran "integraciones externas"
INTEGRATION_MONITORED_PATHS = [
    '/api/external/',
    '/api/erp/',
    '/api/integrations/',
    '/webhook/',
    '/api/payment/',
]

# Mapeo de rutas a tipos de integración (opcional)
INTEGRATION_TYPES = {
    '/api/erp/': 'erp',
    '/api/payment/': 'payment_gateway',
    '/webhook/': 'webhook',
}

# ============================================================================
# APLICAR MIGRACIONES
# ============================================================================

"""
Después de configurar, ejecutar:

1. Aplicar migraciones para crear la tabla application_logs:
   python manage.py migrate django_advanced_logging

2. Verificar que la tabla fue creada:
   python manage.py dbshell
   \dt application_logs
   \d application_logs

3. Probar el logging:
   python manage.py shell
   >>> from django_advanced_logging import get_logger
   >>> logger = get_logger(__name__)
   >>> logger.info("Test desde shell")
   >>> exit()

4. Verificar en PostgreSQL:
   SELECT * FROM application_logs ORDER BY timestamp DESC LIMIT 10;
"""

# ============================================================================
# EJEMPLO DE USO EN TU CÓDIGO
# ============================================================================

"""
# En tus views.py, models.py, services.py, etc.:

from django_advanced_logging import get_logger

logger = get_logger(__name__)

# Logging básico
logger.info("Usuario accedió a la vista")
logger.warning("Advertencia importante")
logger.error("Error en el proceso")

# Logging con campos personalizados (se guardan como JSONB)
logger.info("Orden creada", extra={
    'extra_fields': {
        'order_id': order.id,
        'user_id': request.user.id,
        'total': float(order.total),
        'items_count': order.items.count()
    }
})

# En views
def my_view(request):
    logger.info("Vista accedida", extra={
        'extra_fields': {
            'user_id': request.user.id,
            'path': request.path,
            'method': request.method
        }
    })

    try:
        # Tu lógica
        result = process_data()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True, extra={
            'extra_fields': {
                'user_id': request.user.id,
                'error_type': type(e).__name__
            }
        })
        raise

# Con decorator
from django_advanced_logging import log_execution

@log_execution(log_args=True, log_result=True)
def calculate_total(items):
    return sum(item.price for item in items)
"""

# ============================================================================
# CONSULTAR LOGS EN POSTGRESQL
# ============================================================================

"""
-- Últimos logs
SELECT * FROM application_logs ORDER BY timestamp DESC LIMIT 50;

-- Logs por nivel
SELECT level, COUNT(*) FROM application_logs GROUP BY level;

-- Buscar por campos personalizados (JSONB)
SELECT * FROM application_logs
WHERE extra_data->>'user_id' = '123';

-- Errores recientes
SELECT * FROM application_logs
WHERE level = 'ERROR'
  AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
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

# O puedes mantener ambos sistemas de logging trabajando juntos
