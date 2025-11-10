# __init__.py

"""
Django Advanced Logging
=======================

Sistema de logging profesional y escalable para proyectos Django/Python.

Características:
    - Logging a PostgreSQL de forma asíncrona
    - Múltiples handlers y formatters
    - Middleware para Django
    - Filtros de datos sensibles
    - Soporte para campos personalizados (JSONB)
    - Context managers y decoradores

Instalación:
    pip install django-advanced-logging

Uso básico:
    >>> from django_advanced_logging import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Hello world!")

Documentación completa:
    https://django-advanced-logging.readthedocs.io
"""

from .__version__ import __version__, __author__, __email__

# Importar clases principales
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

# Importar utilidades
from .utils import (
    get_logger,
    get_logger_manager,
    initialize_logging,
)

# Importaciones condicionales de Django
try:
    import django
    _django_available = True
except ImportError:
    _django_available = False

if _django_available:
    try:
        from .django.middleware import LoggingMiddleware
        from .django.apps import DjangoAdvancedLoggingConfig
        __all_django__ = ['LoggingMiddleware', 'DjangoAdvancedLoggingConfig']
    except ImportError:
        __all_django__ = []
else:
    __all_django__ = []

# Definir __all__ para imports explícitos
__all__ = [
    # Versión
    '__version__',
    '__author__',
    '__email__',
    
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
    
    # Utilidades
    'get_logger',
    'get_logger_manager',
    'initialize_logging',
] + __all_django__


# Metadatos
__title__ = 'Django Advanced Logging'
__description__ = 'Sistema de logging profesional y escalable para Django'
__url__ = 'https://github.com/tuusuario/django-advanced-logging'
__license__ = 'MIT'


def get_version() -> str:
    """Retorna la versión del paquete."""
    return __version__

