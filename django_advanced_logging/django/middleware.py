"""
Middlewares de logging para Django.

Este módulo proporciona dos middlewares:
1. LoggingMiddleware - Logging general de todos los requests HTTP
2. ExternalIntegrationLoggingMiddleware - Logging específico para integraciones externas
"""

import time
from django.utils.deprecation import MiddlewareMixin
from django_advanced_logging import get_logger

# Importar middleware de integraciones
from .integrations_middleware import ExternalIntegrationLoggingMiddleware


class LoggingMiddleware(MiddlewareMixin):
    """
    Middleware que registra automáticamente todas las peticiones HTTP.
    
    Características:
        - Registra método, path, usuario, IP
        - Mide tiempo de respuesta
        - Registra código de estado
        - Captura excepciones
    
    Uso en settings.py:
        MIDDLEWARE = [
            ...
            'django_advanced_logging.django.middleware.LoggingMiddleware',
        ]
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = get_logger('middleware.requests')
    
    def process_request(self, request):
        """Procesa el request antes de que llegue a la vista."""
        request._start_time = time.time()
        
        # Log del request entrante
        self.logger.info(
            f"Request entrante: {request.method} {request.path}",
            extra={
                'extra_fields': {
                    'method': request.method,
                    'path': request.path,
                    'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                    'ip': self._get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'content_type': request.content_type
                }
            }
        )
        
        return None
    
    def process_response(self, request, response):
        """Procesa el response antes de devolverlo al cliente."""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log del response
            log_level = 'info' if response.status_code < 400 else 'warning'
            log_method = getattr(self.logger, log_level)
            
            log_method(
                f"Response: {request.method} {request.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s",
                extra={
                    'extra_fields': {
                        'method': request.method,
                        'path': request.path,
                        'status_code': response.status_code,
                        'duration_seconds': round(duration, 3),
                        'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                    }
                }
            )
        
        return response
    
    def process_exception(self, request, exception):
        """Procesa excepciones que ocurren durante el procesamiento."""
        self.logger.error(
            f"Excepción durante {request.method} {request.path}: {str(exception)}",
            exc_info=True,
            extra={
                'extra_fields': {
                    'method': request.method,
                    'path': request.path,
                    'exception_type': type(exception).__name__,
                    'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                }
            }
        )
        
        return None
    
    @staticmethod
    def _get_client_ip(request):
        """Obtiene la IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Exportar ambos middlewares
__all__ = ['LoggingMiddleware', 'ExternalIntegrationLoggingMiddleware']