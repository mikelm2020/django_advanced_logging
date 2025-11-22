"""
Middlewares de logging para Django.

Este modulo proporciona middlewares para logging automatico:
- LoggingMiddleware: Logging general de requests HTTP
- ExternalIntegrationLoggingMiddleware: Logging para integraciones externas
"""

import time
import json
import re
from typing import Optional, Dict, Any, List

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest, HttpResponse


def _get_logger():
    """Obtiene el logger de forma lazy para evitar import circular."""
    from .utils import get_logger
    return get_logger


class LoggingMiddleware(MiddlewareMixin):
    """
    Middleware que registra automaticamente todas las peticiones HTTP.

    Caracteristicas:
        - Registra metodo, path, usuario, IP
        - Mide tiempo de respuesta
        - Registra codigo de estado
        - Captura excepciones

    Uso en settings.py:
        MIDDLEWARE = [
            ...
            'advanced_logging.middleware.LoggingMiddleware',
        ]
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._logger = None

    @property
    def logger(self):
        """Logger lazy-loaded."""
        if self._logger is None:
            self._logger = _get_logger()('middleware.requests')
        return self._logger

    def process_request(self, request: HttpRequest) -> None:
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
                    'content_type': getattr(request, 'content_type', None)
                }
            }
        )

        return None

    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse
    ) -> HttpResponse:
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

    def process_exception(
        self,
        request: HttpRequest,
        exception: Exception
    ) -> None:
        """Procesa excepciones que ocurren durante el procesamiento."""
        self.logger.error(
            f"Excepcion durante {request.method} {request.path}: {str(exception)}",
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
    def _get_client_ip(request: HttpRequest) -> str:
        """Obtiene la IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


class ExternalIntegrationLoggingMiddleware(MiddlewareMixin):
    """
    Middleware especializado para logging de integraciones externas.

    Registra detalladamente las peticiones a endpoints de integraciones
    como ERPs, APIs de pago, webhooks, etc.

    Uso en settings.py:
        MIDDLEWARE = [
            ...
            'advanced_logging.middleware.ExternalIntegrationLoggingMiddleware',
        ]

        # Opcional: Configurar paths monitoreados
        INTEGRATION_MONITORED_PATHS = [
            '/api/erp/',
            '/api/integrations/',
            '/webhook/',
        ]

        INTEGRATION_TYPES = {
            '/api/erp/': 'erp',
            '/api/payment/': 'payment_processor',
            '/webhook/': 'webhook',
        }
    """

    # Paths por defecto a monitorear
    DEFAULT_MONITORED_PATHS: List[str] = [
        '/api/erp/',
        '/api/integrations/',
        '/webhook/',
        '/api/payment/',
        '/api/shipping/',
        '/api/crm/',
        '/api/email/',
        '/api/sms/',
        '/api/notification/',
        '/api/magento/',
        '/api/ecommerce/',
    ]

    # Tipos de integracion por defecto
    DEFAULT_INTEGRATION_TYPES: Dict[str, str] = {
        '/api/erp/': 'erp',
        '/api/payment/': 'payment_processor',
        '/api/shipping/': 'shipping_provider',
        '/api/crm/': 'crm',
        '/webhook/': 'webhook',
        '/api/magento/': 'magento',
        '/api/ecommerce/': 'ecommerce',
        '/api/email/': 'email_service',
        '/api/sms/': 'sms_service',
        '/api/notification/': 'notification_service',
    }

    def __init__(self, get_response):
        self.get_response = get_response
        self._logger = None
        self._monitored_paths = None
        self._integration_types = None

    @property
    def logger(self):
        """Logger lazy-loaded."""
        if self._logger is None:
            self._logger = _get_logger()('middleware.integrations')
        return self._logger

    @property
    def monitored_paths(self) -> List[str]:
        """Paths monitoreados (configurable via settings)."""
        if self._monitored_paths is None:
            from django.conf import settings
            self._monitored_paths = getattr(
                settings,
                'INTEGRATION_MONITORED_PATHS',
                self.DEFAULT_MONITORED_PATHS
            )
        return self._monitored_paths

    @property
    def integration_types(self) -> Dict[str, str]:
        """Tipos de integracion (configurable via settings)."""
        if self._integration_types is None:
            from django.conf import settings
            self._integration_types = getattr(
                settings,
                'INTEGRATION_TYPES',
                self.DEFAULT_INTEGRATION_TYPES
            )
        return self._integration_types

    def _is_integration_endpoint(self, path: str) -> bool:
        """Verifica si el path es un endpoint de integracion."""
        return any(path.startswith(p) for p in self.monitored_paths)

    def _get_integration_type(self, path: str) -> str:
        """Determina el tipo de integracion basado en el path."""
        for prefix, integration_type in self.integration_types.items():
            if path.startswith(prefix):
                return integration_type
        return 'unknown'

    def process_request(self, request: HttpRequest) -> None:
        """Procesa el request para endpoints de integracion."""
        if not self._is_integration_endpoint(request.path):
            return None

        request._integration_start_time = time.time()
        request._integration_type = self._get_integration_type(request.path)

        # Extraer informacion del request
        request_info = self._extract_request_info(request)

        self.logger.info(
            f"Integration request: {request._integration_type} - "
            f"{request.method} {request.path}",
            extra={
                'extra_fields': {
                    'integration_type': request._integration_type,
                    'method': request.method,
                    'path': request.path,
                    'ip': self._get_client_ip(request),
                    **request_info
                }
            }
        )

        return None

    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse
    ) -> HttpResponse:
        """Procesa el response para endpoints de integracion."""
        if not hasattr(request, '_integration_start_time'):
            return response

        duration = time.time() - request._integration_start_time
        log_level = self._get_log_level(response.status_code)

        # Extraer contexto de error si aplica
        error_context = {}
        if response.status_code >= 400:
            error_context = self._extract_error_context(response)

        log_method = getattr(self.logger, log_level)
        log_method(
            f"Integration response: {request._integration_type} - "
            f"Status: {response.status_code} - Duration: {duration:.3f}s",
            extra={
                'extra_fields': {
                    'integration_type': request._integration_type,
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_seconds': round(duration, 3),
                    **error_context
                }
            }
        )

        return response

    def _extract_request_info(self, request: HttpRequest) -> Dict[str, Any]:
        """Extrae informacion relevante del request."""
        info: Dict[str, Any] = {}

        # Headers relevantes para integraciones
        relevant_headers = [
            'HTTP_X_WEBHOOK_ID',
            'HTTP_X_REQUEST_ID',
            'HTTP_X_CORRELATION_ID',
            'HTTP_AUTHORIZATION',
            'HTTP_X_API_KEY',
        ]

        for header in relevant_headers:
            value = request.META.get(header)
            if value:
                # Ocultar valores sensibles
                if 'AUTHORIZATION' in header or 'API_KEY' in header:
                    info[header.lower().replace('http_', '')] = '***'
                else:
                    info[header.lower().replace('http_', '')] = value

        return info

    def _extract_error_context(self, response: HttpResponse) -> Dict[str, Any]:
        """Extrae contexto de error del response."""
        context: Dict[str, Any] = {}

        try:
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8')
                if content:
                    try:
                        data = json.loads(content)
                        if isinstance(data, dict):
                            context['error_message'] = data.get(
                                'error',
                                data.get('message', data.get('detail', ''))
                            )
                            context['error_code'] = data.get('code', '')
                    except json.JSONDecodeError:
                        context['error_message'] = content[:200]
        except Exception:
            pass

        return context

    def _get_log_level(self, status_code: int) -> str:
        """Determina el nivel de log basado en el status code."""
        if status_code < 400:
            return 'info'
        elif status_code < 500:
            return 'warning'
        else:
            return 'error'

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """Obtiene la IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip


# Exportar middlewares
__all__ = ['LoggingMiddleware', 'ExternalIntegrationLoggingMiddleware']
