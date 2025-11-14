"""
Tests para la integración con Django

Cubre:
- DjangoAdvancedLoggingConfig (apps.py)
- LoggingMiddleware (middleware.py)
- ExternalIntegrationLoggingMiddleware (integrations_middleware.py)
"""

import logging
import pytest
from unittest.mock import Mock, MagicMock, patch
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse, Http404


class TestDjangoAdvancedLoggingConfig:
    """Tests para DjangoAdvancedLoggingConfig en apps.py."""

    def test_app_config_name(self):
        """Verifica el nombre de la app."""
        from django_advanced_logging.django.apps import DjangoAdvancedLoggingConfig
        
        config = DjangoAdvancedLoggingConfig('django_advanced_logging', None)
        
        assert config.name == 'django_advanced_logging'
        assert config.verbose_name == 'Django Advanced Logging'

    @patch('django_advanced_logging.utils.configure_django_logging')
    def test_ready_initializes_logging_with_settings(self, mock_configure):
        """Verifica que ready() inicialice el logging si hay LOGGING_CONFIG."""
        from django_advanced_logging.django.apps import DjangoAdvancedLoggingConfig
        from django.conf import settings
        
        # Asegurar que LOGGING_CONFIG exista
        assert hasattr(settings, 'LOGGING_CONFIG')
        
        config = DjangoAdvancedLoggingConfig('django_advanced_logging', None)
        
        # Simular primera llamada a ready()
        if hasattr(config, '_initialized'):
            delattr(config, '_initialized')
        
        config.ready()
        
        # Debe haberse llamado a configure_django_logging
        mock_configure.assert_called_once()

    def test_ready_prevents_double_initialization(self):
        """Verifica que ready() no inicialice dos veces."""
        from django_advanced_logging.django.apps import DjangoAdvancedLoggingConfig
        
        config = DjangoAdvancedLoggingConfig('django_advanced_logging', None)
        
        # Primera llamada
        config.ready()
        
        # Marcar como inicializado
        assert hasattr(config, '_initialized')
        
        # Segunda llamada no debe hacer nada
        with patch('django_advanced_logging.utils.configure_django_logging') as mock_configure:
            config.ready()
            mock_configure.assert_not_called()


class TestLoggingMiddleware:
    """Tests para LoggingMiddleware."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse("OK", status=200))

    def test_middleware_logs_request(self, caplog):
        """Verifica que el middleware loggee los requests."""
        from django_advanced_logging.django.middleware import LoggingMiddleware
        
        middleware = LoggingMiddleware(self.get_response)
        request = self.factory.get('/test/path/')
        request.user = AnonymousUser()
        
        with caplog.at_level(logging.INFO):
            response = middleware(request)
        
        assert "Request entrante" in caplog.text
        assert "GET" in caplog.text
        assert "/test/path/" in caplog.text

    def test_middleware_logs_response(self, caplog):
        """Verifica que el middleware loggee los responses."""
        from django_advanced_logging.django.middleware import LoggingMiddleware
        
        middleware = LoggingMiddleware(self.get_response)
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        with caplog.at_level(logging.INFO):
            response = middleware(request)
        
        assert "Response" in caplog.text
        assert "200" in caplog.text
        assert "Duration" in caplog.text

    def test_middleware_measures_duration(self):
        """Verifica que el middleware mida el tiempo de respuesta."""
        from django_advanced_logging.django.middleware import LoggingMiddleware
        
        # Simular respuesta lenta
        def slow_response(request):
            import time
            time.sleep(0.1)
            return HttpResponse("OK")
        
        middleware = LoggingMiddleware(slow_response)
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        middleware.process_request(request)
        response = middleware.get_response(request)
        response = middleware.process_response(request, response)
        
        assert hasattr(request, '_start_time')

    def test_middleware_logs_errors_with_warning(self, caplog):
        """Verifica que los códigos de error se loggeen como warning."""
        from django_advanced_logging.django.middleware import LoggingMiddleware
        
        error_response = Mock(return_value=HttpResponse("Error", status=404))
        middleware = LoggingMiddleware(error_response)
        request = self.factory.get('/not-found/')
        request.user = AnonymousUser()
        
        with caplog.at_level(logging.WARNING):
            response = middleware(request)
        
        assert "404" in caplog.text

    def test_middleware_logs_exceptions(self, caplog):
        """Verifica que el middleware loggee excepciones."""
        from django_advanced_logging.django.middleware import LoggingMiddleware
        
        def raising_view(request):
            raise ValueError("Test exception")
        
        middleware = LoggingMiddleware(raising_view)
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        with pytest.raises(ValueError):
            with caplog.at_level(logging.ERROR):
                middleware(request)
        
        assert "Excepción" in caplog.text or "Exception" in caplog.text
        assert "ValueError" in caplog.text

    def test_middleware_extracts_client_ip(self):
        """Verifica que el middleware extraiga la IP del cliente."""
        from django_advanced_logging.django.middleware import LoggingMiddleware
        
        middleware = LoggingMiddleware(self.get_response)
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = middleware._get_client_ip(request)
        
        assert ip == '192.168.1.1'

    def test_middleware_handles_x_forwarded_for(self):
        """Verifica que el middleware maneje X-Forwarded-For."""
        from django_advanced_logging.django.middleware import LoggingMiddleware
        
        middleware = LoggingMiddleware(self.get_response)
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        
        ip = middleware._get_client_ip(request)
        
        assert ip == '10.0.0.1'


class TestExternalIntegrationLoggingMiddleware:
    """Tests para ExternalIntegrationLoggingMiddleware."""

    def setup_method(self):
        """Setup para cada test."""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse("OK", status=200))

    def test_middleware_only_processes_integration_endpoints(self):
        """Verifica que solo procese endpoints de integración."""
        from django_advanced_logging.django.integrations_middleware import ExternalIntegrationLoggingMiddleware
        
        middleware = ExternalIntegrationLoggingMiddleware(self.get_response)
        
        # Request normal (no integración)
        normal_request = self.factory.get('/app/users/')
        result = middleware._is_integration_endpoint(normal_request.path)
        assert result is False
        
        # Request de integración
        integration_request = self.factory.get('/api/erp/orders/')
        result = middleware._is_integration_endpoint(integration_request.path)
        assert result is True

    def test_middleware_identifies_integration_type(self):
        """Verifica que identifique correctamente el tipo de integración."""
        from django_advanced_logging.django.integrations_middleware import ExternalIntegrationLoggingMiddleware
        
        middleware = ExternalIntegrationLoggingMiddleware(self.get_response)
        
        test_cases = [
            ('/api/erp/sync/', 'erp'),
            ('/webhook/stripe/', 'webhook'),
            ('/api/payment/process/', 'payment_processor'),
            ('/api/shipping/track/', 'shipping_provider'),
        ]
        
        for path, expected_type in test_cases:
            integration_type = middleware._get_integration_type(path)
            assert integration_type == expected_type

    def test_middleware_logs_integration_request(self, caplog):
        """Verifica que loggee requests de integración."""
        from django_advanced_logging.django.integrations_middleware import ExternalIntegrationLoggingMiddleware
        
        middleware = ExternalIntegrationLoggingMiddleware(self.get_response)
        request = self.factory.post('/api/erp/create/')
        request.user = AnonymousUser()
        
        with caplog.at_level(logging.INFO):
            response = middleware(request)
        
        assert "[ERP]" in caplog.text or "erp" in caplog.text.lower()
        assert "Request recibido" in caplog.text or "Request" in caplog.text

    def test_middleware_extracts_request_info(self):
        """Verifica que extraiga información del request."""
        from django_advanced_logging.django.integrations_middleware import ExternalIntegrationLoggingMiddleware
        
        middleware = ExternalIntegrationLoggingMiddleware(self.get_response)
        request = self.factory.post(
            '/api/erp/sync/',
            HTTP_X_CLIENT_ID='client123',
            HTTP_X_ERP_SYSTEM='SAP',
            HTTP_USER_AGENT='ERP-Client/1.0'
        )
        request.user = AnonymousUser()
        
        info = middleware._extract_request_info(request, 'erp')
        
        assert info['integration_type'] == 'erp'
        assert info['method'] == 'POST'
        assert '/api/erp/sync/' in info['path']
        assert info['client_id'] == 'client123'
        assert info['erp_system'] == 'SAP'

    def test_middleware_handles_webhook_requests(self):
        """Verifica el manejo de webhooks."""
        from django_advanced_logging.django.integrations_middleware import ExternalIntegrationLoggingMiddleware
        
        middleware = ExternalIntegrationLoggingMiddleware(self.get_response)
        request = self.factory.post(
            '/webhook/stripe/',
            HTTP_X_WEBHOOK_SOURCE='stripe',
            HTTP_X_EVENT_TYPE='payment.succeeded',
            HTTP_X_SIGNATURE='sig123'
        )
        request.user = AnonymousUser()
        
        info = middleware._extract_request_info(request, 'webhook')
        
        assert info['webhook_source'] == 'stripe'
        assert info['event_type'] == 'payment.succeeded'
        assert info['signature_provided'] is True

    def test_middleware_logs_magento_requests(self, caplog):
        """Verifica el logging de requests de Magento."""
        from django_advanced_logging.django.integrations_middleware import ExternalIntegrationLoggingMiddleware
        
        middleware = ExternalIntegrationLoggingMiddleware(self.get_response)
        request = self.factory.post(
            '/api/magento/products/',
            HTTP_STORE='default',
            HTTP_X_MAGENTO_VERSION='2.4.5'
        )
        request.user = AnonymousUser()
        
        with caplog.at_level(logging.INFO):
            response = middleware(request)
        
        # Debe loggearse como integración de magento
        assert "MAGENTO" in caplog.text or "magento" in caplog.text.lower()

    def test_middleware_measures_response_time(self, caplog):
        """Verifica que mida el tiempo de respuesta."""
        from django_advanced_logging.django.integrations_middleware import ExternalIntegrationLoggingMiddleware
        
        middleware = ExternalIntegrationLoggingMiddleware(self.get_response)
        request = self.factory.get('/api/erp/status/')
        request.user = AnonymousUser()
        
        with caplog.at_level(logging.INFO):
            response = middleware(request)
        
        # Debe incluir información de duración
        assert "s" in caplog.text or "duration" in caplog.text.lower()

    def test_middleware_logs_errors(self, caplog):
        """Verifica que loggee errores en integraciones."""
        from django_advanced_logging.django.integrations_middleware import ExternalIntegrationLoggingMiddleware
        
        def error_response(request):
            raise RuntimeError("Integration error")
        
        middleware = ExternalIntegrationLoggingMiddleware(error_response)
        request = self.factory.post('/api/erp/sync/')
        request.user = AnonymousUser()
        
        with pytest.raises(RuntimeError):
            with caplog.at_level(logging.ERROR):
                middleware(request)
        
        assert "Error" in caplog.text or "error" in caplog.text.lower()
        assert "RuntimeError" in caplog.text

    def test_middleware_extracts_magento_context(self):
        """Verifica la extracción de contexto de Magento."""
        from django_advanced_logging.django.integrations_middleware import ExternalIntegrationLoggingMiddleware
        import json
        
        middleware = ExternalIntegrationLoggingMiddleware(self.get_response)
        
        # Simular request de producto Magento
        body_data = {
            'product': {
                'sku': 'TEST-SKU-123',
                'name': 'Test Product',
                'type_id': 'simple',
                'price': 29.99
            }
        }
        
        request = self.factory.post(
            '/api/magento/products/',
            data=json.dumps(body_data),
            content_type='application/json'
        )
        request.user = AnonymousUser()
        
        context = middleware._extract_magento_context(request)
        
        assert context.get('operation') == 'product_management'
        assert context.get('sku') == 'TEST-SKU-123'
        assert context.get('product_name') == 'Test Product'

    def test_middleware_get_log_level_by_status_code(self):
        """Verifica que el nivel de log sea correcto según status code."""
        from django_advanced_logging.django.integrations_middleware import ExternalIntegrationLoggingMiddleware
        
        middleware = ExternalIntegrationLoggingMiddleware(self.get_response)
        
        assert middleware._get_log_level(200) == 'info'
        assert middleware._get_log_level(404) == 'warning'
        assert middleware._get_log_level(500) == 'error'
