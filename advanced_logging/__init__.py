"""
Advanced Logging - App Django Auto-contenida
============================================

Sistema de logging profesional y escalable para proyectos Django.

Caracteristicas:
    - Logging a PostgreSQL de forma asincrona
    - Multiples handlers y formatters
    - Middleware para Django
    - Filtros de datos sensibles
    - Soporte para campos personalizados (JSONB)
    - Context managers y decoradores
    - Admin para visualizar logs

Instalacion:
    1. Copia la carpeta 'advanced_logging' a tu proyecto Django
    2. Agrega 'advanced_logging' a INSTALLED_APPS
    3. Ejecuta: python manage.py migrate
    4. Opcionalmente agrega el middleware a MIDDLEWARE

Uso basico:
    >>> from advanced_logging import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Hello world!")

Configuracion en settings.py (opcional):
    ADVANCED_LOGGING = {
        'name': 'my_project',
        'level': 'DEBUG',
        'environment': 'development',
        'console_output': True,
        'file_output': False,
        'json_format': False,
        'postgres_enabled': True,
    }
"""

__version__ = '2.0.0'
__author__ = 'Tu Nombre'

# Core classes
from .core.logger import (
    LoggerManager,
    LogConfig,
    LogLevel,
    Environment,
)

from .core.handlers import (
    PostgreSQLHandler,
    PostgreSQLConfig,
)

from .core.formatters import (
    ColoredFormatter,
    JSONFormatter,
)

from .core.filters import (
    EnvironmentFilter,
    SensitiveDataFilter,
)

# Utilities
from .utils import (
    get_logger,
    get_logger_manager,
    initialize_logging,
    reset_logging,
    log_execution,
)

# Django integration
from .middleware import (
    LoggingMiddleware,
    ExternalIntegrationLoggingMiddleware,
)

# App config
default_app_config = 'advanced_logging.apps.AdvancedLoggingConfig'

__all__ = [
    # Version
    '__version__',
    '__author__',

    # Core
    'LoggerManager',
    'LogConfig',
    'LogLevel',
    'Environment',

    # Handlers
    'PostgreSQLHandler',
    'PostgreSQLConfig',

    # Formatters
    'ColoredFormatter',
    'JSONFormatter',

    # Filters
    'EnvironmentFilter',
    'SensitiveDataFilter',

    # Utilities
    'get_logger',
    'get_logger_manager',
    'initialize_logging',
    'reset_logging',
    'log_execution',

    # Middleware
    'LoggingMiddleware',
    'ExternalIntegrationLoggingMiddleware',
]
