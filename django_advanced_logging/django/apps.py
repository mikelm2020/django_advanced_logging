# apps.py

"""
Configuración de la aplicación Django para django-advanced-logging.

Para usar este paquete en Django, agrega 'django_advanced_logging' 
a INSTALLED_APPS en tu settings.py
"""

try:
    from django.apps import AppConfig
    from django.conf import settings
except ImportError:
    raise ImportError(
        "Django no está instalado. "
        "Instala con: pip install django o poetry add django"
    )


class DjangoAdvancedLoggingConfig(AppConfig):
    """Configuración de la app Django Advanced Logging."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_advanced_logging'
    verbose_name = 'Django Advanced Logging'
    
    def ready(self):
        """
        Se ejecuta cuando Django inicializa la app.
        Aquí inicializamos el sistema de logging.
        """
        # Evitar inicialización múltiple
        if hasattr(self, '_initialized'):
            return

        self._initialized = True

        # Obtener configuración de logging
        logging_config = getattr(settings, 'LOGGING_CONFIG', None)

        # Si no hay configuración explícita, crear una por defecto
        if logging_config is None:
            logging_config = self._get_default_config()

        # Auto-configurar PostgreSQL si está habilitado y no configurado manualmente
        if logging_config.get('postgres_enabled') and not logging_config.get('postgres_config'):
            logging_config['postgres_config'] = self._get_postgres_config_from_django()

        # Inicializar el sistema de logging
        from ..utils import configure_django_logging

        try:
            configure_django_logging(settings, config=None, **logging_config)

            # Log de inicio
            from ..utils import get_logger
            logger = get_logger('django_advanced_logging')
            logger.info(
                "Django Advanced Logging inicializado",
                extra={
                    'extra_fields': {
                        'environment': logging_config.get('environment', 'unknown'),
                        'debug': settings.DEBUG,
                        'postgres_enabled': logging_config.get('postgres_enabled', False)
                    }
                }
            )
        except Exception as e:
            import sys
            print(f"Error al inicializar Django Advanced Logging: {e}", file=sys.stderr)

    def _get_default_config(self):
        """Retorna configuración por defecto basada en variables de entorno."""
        import os

        return {
            'name': os.getenv('LOG_NAME', 'django_app'),
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'environment': os.getenv('LOG_ENVIRONMENT', 'production' if not settings.DEBUG else 'development'),
            'console_output': os.getenv('LOG_CONSOLE', 'true').lower() == 'true',
            'file_output': os.getenv('LOG_FILE', 'false').lower() == 'true',
            'json_format': os.getenv('LOG_JSON', 'false' if settings.DEBUG else 'true').lower() == 'true',
            'postgres_enabled': os.getenv('POSTGRES_ENABLED', 'false').lower() == 'true',
        }

    def _get_postgres_config_from_django(self):
        """
        Extrae la configuración de PostgreSQL desde Django DATABASES.
        Usa la misma base de datos del proyecto Django.
        """
        import os

        # Obtener configuración de la base de datos de Django
        db_config = settings.DATABASES.get('default', {})

        # Verificar que sea PostgreSQL
        engine = db_config.get('ENGINE', '')
        if 'postgresql' not in engine and 'postgis' not in engine:
            print("Warning: PostgreSQL logging habilitado pero la base de datos no es PostgreSQL")
            return None

        return {
            'host': db_config.get('HOST', os.getenv('LOG_DB_HOST', 'localhost')),
            'port': int(db_config.get('PORT', os.getenv('LOG_DB_PORT', '5432'))),
            'database': db_config.get('NAME', os.getenv('LOG_DB_NAME', 'django_db')),
            'user': db_config.get('USER', os.getenv('LOG_DB_USER', 'postgres')),
            'password': db_config.get('PASSWORD', os.getenv('LOG_DB_PASSWORD', '')),
            'table_name': os.getenv('LOG_DB_TABLE', 'application_logs'),
            'schema': 'public',
            'buffer_size': int(os.getenv('LOG_BUFFER_SIZE', '1000')),
            'batch_size': int(os.getenv('LOG_BATCH_SIZE', '10')),
            'flush_interval': float(os.getenv('LOG_FLUSH_INTERVAL', '5.0')),
        }
