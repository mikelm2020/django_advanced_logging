"""
Configuracion de la aplicacion Django Advanced Logging.

Para usar esta app en Django:
1. Copia la carpeta 'advanced_logging' a tu proyecto
2. Agrega 'advanced_logging' a INSTALLED_APPS
3. Ejecuta 'python manage.py migrate'
4. Opcionalmente configura ADVANCED_LOGGING en settings.py
"""

from django.apps import AppConfig
from django.conf import settings


class AdvancedLoggingConfig(AppConfig):
    """Configuracion de la app Advanced Logging."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'advanced_logging'
    verbose_name = 'Advanced Logging'

    def ready(self):
        """
        Se ejecuta cuando Django inicializa la app.
        Aqui inicializamos el sistema de logging.
        """
        # Evitar inicializacion multiple
        if hasattr(self, '_initialized'):
            return

        self._initialized = True

        # Obtener configuracion de logging desde settings
        logging_config = getattr(settings, 'ADVANCED_LOGGING', None)

        # Si no hay configuracion explicita, crear una por defecto
        if logging_config is None:
            logging_config = self._get_default_config()

        # Auto-configurar PostgreSQL si esta habilitado
        if logging_config.get('postgres_enabled') and not logging_config.get('postgres_config'):
            postgres_config = self._get_postgres_config_from_django()
            if postgres_config:
                logging_config['postgres_config'] = postgres_config

        # Inicializar el sistema de logging
        from .utils import initialize_logging

        try:
            initialize_logging(**logging_config)

            # Log de inicio
            from .utils import get_logger
            logger = get_logger('advanced_logging')
            logger.info(
                "Advanced Logging inicializado",
                extra={
                    'extra_fields': {
                        'environment': logging_config.get('environment', 'unknown'),
                        'debug': getattr(settings, 'DEBUG', False),
                        'postgres_enabled': logging_config.get('postgres_enabled', False)
                    }
                }
            )
        except Exception as e:
            import sys
            print(f"Error al inicializar Advanced Logging: {e}", file=sys.stderr)

    def _get_default_config(self):
        """Retorna configuracion por defecto basada en variables de entorno."""
        import os

        debug = getattr(settings, 'DEBUG', False)

        return {
            'name': os.getenv('LOG_NAME', 'django_app'),
            'level': os.getenv('LOG_LEVEL', 'DEBUG' if debug else 'INFO'),
            'environment': os.getenv(
                'LOG_ENVIRONMENT',
                'development' if debug else 'production'
            ),
            'console_output': os.getenv('LOG_CONSOLE', 'true').lower() == 'true',
            'file_output': os.getenv('LOG_FILE', 'false').lower() == 'true',
            'json_format': os.getenv(
                'LOG_JSON',
                'false' if debug else 'true'
            ).lower() == 'true',
            'postgres_enabled': os.getenv('POSTGRES_ENABLED', 'false').lower() == 'true',
        }

    def _get_postgres_config_from_django(self):
        """
        Extrae la configuracion de PostgreSQL desde Django DATABASES.
        Usa la misma base de datos del proyecto Django.
        """
        import os

        # Obtener configuracion de la base de datos de Django
        databases = getattr(settings, 'DATABASES', {})
        db_config = databases.get('default', {})

        # Verificar que sea PostgreSQL
        engine = db_config.get('ENGINE', '')
        if 'postgresql' not in engine and 'postgis' not in engine:
            return None

        return {
            'host': db_config.get('HOST', os.getenv('LOG_DB_HOST', 'localhost')),
            'port': int(db_config.get('PORT') or os.getenv('LOG_DB_PORT', '5432')),
            'database': db_config.get('NAME', os.getenv('LOG_DB_NAME', 'django_db')),
            'user': db_config.get('USER', os.getenv('LOG_DB_USER', 'postgres')),
            'password': db_config.get('PASSWORD', os.getenv('LOG_DB_PASSWORD', '')),
            'table_name': os.getenv('LOG_DB_TABLE', 'advanced_logging_applicationlog'),
            'schema': 'public',
            'buffer_size': int(os.getenv('LOG_BUFFER_SIZE', '1000')),
            'batch_size': int(os.getenv('LOG_BATCH_SIZE', '10')),
            'flush_interval': float(os.getenv('LOG_FLUSH_INTERVAL', '5.0')),
        }
