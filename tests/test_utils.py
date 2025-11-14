"""
Tests para el módulo utils.py

Cubre:
- initialize_logging
- initialize_from_env
- get_logger
- get_logger_manager
- reset_logging
- log_execution (decorator)
- configure_django_logging
"""

import os
import logging
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from django_advanced_logging import (
    utils,
    get_logger,
    get_logger_manager,
    initialize_logging,
    LogConfig,
    LogLevel,
    Environment,
)


class TestInitializeLogging:
    """Tests para initialize_logging()."""

    def test_initialize_with_config(self, sample_log_config):
        """Verifica que se pueda inicializar con un LogConfig."""
        manager = initialize_logging(sample_log_config)
        
        assert manager is not None
        assert manager.config == sample_log_config

    def test_initialize_with_kwargs(self):
        """Verifica que se pueda inicializar con kwargs."""
        manager = initialize_logging(
            name="test_app",
            level=LogLevel.DEBUG,
            environment=Environment.PRODUCTION
        )
        
        assert manager is not None
        assert manager.config.name == "test_app"
        assert manager.config.level == LogLevel.DEBUG
        assert manager.config.environment == Environment.PRODUCTION

    def test_initialize_sets_global_manager(self, sample_log_config):
        """Verifica que se establezca el manager global."""
        manager = initialize_logging(sample_log_config)
        
        assert utils._logger_manager is manager


class TestInitializeFromEnv:
    """Tests para initialize_from_env()."""

    def test_initialize_from_environment_variables(self, monkeypatch, temp_log_dir):
        """Verifica que se pueda inicializar desde variables de entorno."""
        monkeypatch.setenv('LOG_NAME', 'env_test')
        monkeypatch.setenv('LOG_LEVEL', 'WARNING')
        monkeypatch.setenv('LOG_ENVIRONMENT', 'staging')
        monkeypatch.setenv('LOG_DIR', str(temp_log_dir))
        monkeypatch.setenv('LOG_JSON', 'true')
        
        from django_advanced_logging.utils import initialize_from_env
        manager = initialize_from_env()
        
        assert manager.config.name == 'env_test'
        assert manager.config.level == LogLevel.WARNING
        assert manager.config.environment == 'staging'
        assert manager.config.json_format is True

    def test_initialize_with_postgres_from_env(self, monkeypatch):
        """Verifica que se pueda configurar PostgreSQL desde env."""
        monkeypatch.setenv('POSTGRES_ENABLED', 'true')
        monkeypatch.setenv('LOG_DB_HOST', 'db.example.com')
        monkeypatch.setenv('LOG_DB_PORT', '5433')
        monkeypatch.setenv('LOG_DB_NAME', 'my_logs')
        monkeypatch.setenv('LOG_DB_USER', 'logger')
        monkeypatch.setenv('LOG_DB_PASSWORD', 'secret')
        monkeypatch.setenv('LOG_DB_TABLE', 'custom_logs')
        
        from django_advanced_logging.utils import initialize_from_env
        with patch('psycopg2.connect'):
            manager = initialize_from_env()
        
        assert manager.config.postgres_enabled is True
        assert manager.config.postgres_config.host == 'db.example.com'
        assert manager.config.postgres_config.port == 5433
        assert manager.config.postgres_config.database == 'my_logs'


class TestGetLogger:
    """Tests para get_logger()."""

    def test_get_logger_auto_initializes(self):
        """Verifica que get_logger() inicialice automáticamente si es necesario."""
        utils._logger_manager = None
        
        logger = get_logger('test_module')
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert utils._logger_manager is not None

    def test_get_logger_returns_configured_logger(self, sample_log_config):
        """Verifica que get_logger() retorne un logger configurado."""
        initialize_logging(sample_log_config)
        
        logger = get_logger('my_module')
        
        assert isinstance(logger, logging.Logger)
        assert 'my_module' in logger.name

    def test_get_logger_without_name(self, sample_log_config):
        """Verifica que get_logger() funcione sin nombre."""
        initialize_logging(sample_log_config)
        
        logger = get_logger()
        
        assert isinstance(logger, logging.Logger)


class TestGetLoggerManager:
    """Tests para get_logger_manager()."""

    def test_get_logger_manager_returns_instance(self, sample_log_config):
        """Verifica que retorne la instancia del manager."""
        manager = initialize_logging(sample_log_config)
        
        retrieved_manager = get_logger_manager()
        
        assert retrieved_manager is manager

    def test_get_logger_manager_returns_none_when_not_initialized(self):
        """Verifica que retorne None si no está inicializado."""
        utils._logger_manager = None
        
        manager = get_logger_manager()
        
        assert manager is None


class TestResetLogging:
    """Tests para reset_logging()."""

    def test_reset_clears_global_manager(self, sample_log_config):
        """Verifica que reset_logging() limpie el manager global."""
        initialize_logging(sample_log_config)
        
        assert utils._logger_manager is not None
        
        from django_advanced_logging.utils import reset_logging
        reset_logging()
        
        assert utils._logger_manager is None


class TestLogExecutionDecorator:
    """Tests para el decorador log_execution()."""

    def test_decorator_logs_function_execution(self, sample_log_config, caplog):
        """Verifica que el decorador loggee la ejecución de funciones."""
        initialize_logging(sample_log_config)
        
        from django_advanced_logging.utils import log_execution
        
        @log_execution()
        def test_function(x, y):
            return x + y
        
        with caplog.at_level(logging.DEBUG):
            result = test_function(2, 3)
        
        assert result == 5
        assert 'test_function' in caplog.text
        assert 'Ejecutando' in caplog.text

    def test_decorator_with_custom_logger_name(self, sample_log_config, caplog):
        """Verifica que el decorador funcione con un logger personalizado."""
        initialize_logging(sample_log_config)
        
        from django_advanced_logging.utils import log_execution
        
        @log_execution(logger_name='custom.logger', level='INFO')
        def test_function():
            return "done"
        
        with caplog.at_level(logging.INFO):
            result = test_function()
        
        assert result == "done"
        assert 'test_function' in caplog.text

    def test_decorator_logs_exceptions(self, sample_log_config, caplog):
        """Verifica que el decorador loggee excepciones."""
        initialize_logging(sample_log_config)
        
        from django_advanced_logging.utils import log_execution
        
        @log_execution()
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            with caplog.at_level(logging.ERROR):
                failing_function()
        
        assert 'Error en failing_function' in caplog.text
        assert 'ValueError' in caplog.text

    def test_decorator_preserves_function_metadata(self):
        """Verifica que el decorador preserve los metadatos de la función."""
        from django_advanced_logging.utils import log_execution
        
        @log_execution()
        def documented_function():
            """This is a documented function."""
            pass
        
        assert documented_function.__name__ == 'documented_function'
        assert documented_function.__doc__ == "This is a documented function."


class TestConfigureDjangoLogging:
    """Tests para configure_django_logging()."""

    def test_configure_from_django_settings(self, temp_log_dir):
        """Verifica que se pueda configurar desde Django settings."""
        from django.conf import settings
        
        # Simular settings
        mock_settings = Mock()
        mock_settings.LOGGING_CONFIG = {
            'name': 'django_app',
            'level': LogLevel.INFO,
            'environment': Environment.PRODUCTION
        }
        mock_settings.BASE_DIR = temp_log_dir
        
        from django_advanced_logging.utils import configure_django_logging
        manager = configure_django_logging(mock_settings)
        
        assert manager is not None
        assert manager.config.name == 'django_app'

    def test_configure_with_custom_config(self, sample_log_config):
        """Verifica que se pueda pasar un config personalizado."""
        mock_settings = Mock()
        
        from django_advanced_logging.utils import configure_django_logging
        manager = configure_django_logging(mock_settings, config=sample_log_config)
        
        assert manager is not None
        assert manager.config == sample_log_config

    def test_configure_with_kwargs(self):
        """Verifica que se puedan pasar kwargs adicionales."""
        mock_settings = Mock()
        mock_settings.LOGGING_CONFIG = {
            'name': 'base_app'
        }
        
        from django_advanced_logging.utils import configure_django_logging
        manager = configure_django_logging(
            mock_settings,
            level=LogLevel.DEBUG
        )
        
        assert manager.config.level == LogLevel.DEBUG
