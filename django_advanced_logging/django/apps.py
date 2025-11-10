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
        
        # Inicializar logging si está configurado en settings
        if hasattr(settings, 'LOGGING_CONFIG'):
            from ..utils import configure_django_logging
            
            try:
                configure_django_logging(settings)
                
                # Log de inicio
                from ..utils import get_logger
                logger = get_logger('django_advanced_logging')
                logger.info(
                    "Django Advanced Logging inicializado",
                    extra={
                        'extra_fields': {
                            'environment': getattr(settings, 'LOG_ENVIRONMENT', 'unknown'),
                            'debug': settings.DEBUG
                        }
                    }
                )
            except Exception as e:
                import sys
                print(f"Error al inicializar Django Advanced Logging: {e}", file=sys.stderr)
