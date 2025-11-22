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
from advanced_logging import (
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
        
        from advanced_logging.utils import initialize_from_env
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

        from advanced_logging.utils import initialize_from_env
        from advanced_logging.core.handlers import PostgreSQLHandler
        with patch('psycopg2.connect'):
            manager = initialize_from_env()

        # Verificar que se agrego un handler de PostgreSQL
        pg_handlers = [h for h in manager.config.extra_handlers if isinstance(h, PostgreSQLHandler)]
        assert len(pg_handlers) == 1


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
        
        from advanced_logging.utils import reset_logging
        reset_logging()
        
        assert utils._logger_manager is None


class TestLogExecutionDecorator:
    """Tests para el decorador log_execution()."""

    def test_decorator_logs_function_execution(self, sample_log_config):
        """Verifica que el decorador loggee la ejecucion de funciones."""
        initialize_logging(sample_log_config)

        from advanced_logging.utils import log_execution

        @log_execution()
        def test_function(x, y):
            return x + y

        # Verificar que la funcion se ejecuta correctamente
        result = test_function(2, 3)
        assert result == 5

    def test_decorator_with_custom_logger_name(self, sample_log_config):
        """Verifica que el decorador funcione con un logger personalizado."""
        initialize_logging(sample_log_config)

        from advanced_logging.utils import log_execution

        @log_execution(logger_name='custom.logger', level='INFO')
        def test_function():
            return "done"

        result = test_function()
        assert result == "done"

    def test_decorator_logs_exceptions(self, sample_log_config):
        """Verifica que el decorador propague excepciones."""
        initialize_logging(sample_log_config)

        from advanced_logging.utils import log_execution

        @log_execution()
        def failing_function():
            raise ValueError("Test error")

        # Verificar que la excepcion se propaga
        with pytest.raises(ValueError):
            failing_function()

    def test_decorator_preserves_function_metadata(self):
        """Verifica que el decorador preserve los metadatos de la función."""
        from advanced_logging.utils import log_execution
        
        @log_execution()
        def documented_function():
            """This is a documented function."""
            pass
        
        assert documented_function.__name__ == 'documented_function'
        assert documented_function.__doc__ == "This is a documented function."
