"""
Tests para el módulo core/logger.py

Cubre:
- LogLevel
- Environment
- LogConfig
- LoggerManager
"""

import logging
import os
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock

from advanced_logging import (
    LogConfig,
    LogLevel,
    Environment,
    LoggerManager,
)


class TestLogLevel:
    """Tests para la clase LogLevel."""

    def test_log_levels_values(self):
        """Verifica que los niveles de log tengan los valores correctos."""
        assert LogLevel.DEBUG == logging.DEBUG == 10
        assert LogLevel.INFO == logging.INFO == 20
        assert LogLevel.WARNING == logging.WARNING == 30
        assert LogLevel.ERROR == logging.ERROR == 40
        assert LogLevel.CRITICAL == logging.CRITICAL == 50


class TestEnvironment:
    """Tests para la clase Environment."""

    def test_environment_constants(self):
        """Verifica que las constantes de entorno existan."""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"


class TestLogConfig:
    """Tests para la dataclass LogConfig."""

    def test_default_config(self):
        """Verifica que la configuración por defecto sea correcta."""
        config = LogConfig()

        assert config.name == "app"
        assert config.level == LogLevel.INFO
        assert config.environment == Environment.DEVELOPMENT
        assert config.console_output is True
        assert config.file_output is True
        assert config.rotate_logs is True
        assert config.max_bytes == 10 * 1024 * 1024  # 10 MB
        assert config.backup_count == 5
        assert config.json_format is False
        assert config.mask_sensitive is True

    def test_custom_config(self):
        """Verifica que se pueda crear una configuración personalizada."""
        config = LogConfig(
            name="my_app",
            level=LogLevel.DEBUG,
            environment=Environment.PRODUCTION,
            json_format=True,
            max_bytes=5 * 1024 * 1024
        )

        assert config.name == "my_app"
        assert config.level == LogLevel.DEBUG
        assert config.environment == Environment.PRODUCTION
        assert config.json_format is True
        assert config.max_bytes == 5 * 1024 * 1024

    def test_config_with_log_dir(self, temp_log_dir):
        """Verifica que se pueda configurar un directorio de logs."""
        config = LogConfig(log_dir=temp_log_dir)

        assert config.log_dir == temp_log_dir
        assert isinstance(config.log_dir, Path)


class TestLoggerManager:
    """Tests para la clase LoggerManager."""

    def test_singleton_pattern(self, sample_log_config):
        """Verifica que LoggerManager implemente el patrón Singleton."""
        manager1 = LoggerManager(sample_log_config)
        manager2 = LoggerManager(sample_log_config)

        assert manager1 is manager2

    def test_different_configs_different_instances(self):
        """Verifica que configs diferentes creen instancias diferentes."""
        config1 = LogConfig(name="app1", environment=Environment.DEVELOPMENT)
        config2 = LogConfig(name="app2", environment=Environment.DEVELOPMENT)

        manager1 = LoggerManager(config1)
        manager2 = LoggerManager(config2)

        assert manager1 is not manager2

    def test_same_name_different_env_different_instances(self):
        """Verifica que mismo nombre pero diferente entorno creen instancias diferentes."""
        config1 = LogConfig(name="app", environment=Environment.DEVELOPMENT)
        config2 = LogConfig(name="app", environment=Environment.PRODUCTION)

        manager1 = LoggerManager(config1)
        manager2 = LoggerManager(config2)

        assert manager1 is not manager2

    def test_get_logger(self, sample_log_config):
        """Verifica que se pueda obtener un logger."""
        manager = LoggerManager(sample_log_config)
        logger = manager.get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_app.test_module"

    def test_get_logger_without_name(self, sample_log_config):
        """Verifica que se pueda obtener un logger sin nombre específico."""
        manager = LoggerManager(sample_log_config)
        logger = manager.get_logger()

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_app"

    def test_get_logger_cached(self, sample_log_config):
        """Verifica que los loggers se cacheen."""
        manager = LoggerManager(sample_log_config)

        logger1 = manager.get_logger("test_module")
        logger2 = manager.get_logger("test_module")

        assert logger1 is logger2

    def test_logger_has_correct_level(self):
        """Verifica que el logger tenga el nivel correcto."""
        config = LogConfig(name="test", level=LogLevel.WARNING)
        manager = LoggerManager(config)
        logger = manager.get_logger()

        # El root logger debe tener el nivel configurado
        root_logger = logging.getLogger("test")
        assert root_logger.level == LogLevel.WARNING

    def test_console_handler_created(self, sample_log_config):
        """Verifica que se cree el handler de consola."""
        sample_log_config.console_output = True
        manager = LoggerManager(sample_log_config)

        root_logger = logging.getLogger(sample_log_config.name)
        handlers = root_logger.handlers

        assert len(handlers) > 0
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)

    def test_file_handler_created(self, temp_log_dir):
        """Verifica que se cree el handler de archivo."""
        config = LogConfig(
            name="test_file",
            log_dir=temp_log_dir,
            console_output=False,
            file_output=True
        )
        manager = LoggerManager(config)

        root_logger = logging.getLogger(config.name)
        handlers = root_logger.handlers

        assert len(handlers) > 0
        assert any(
            isinstance(h, (logging.FileHandler, logging.handlers.RotatingFileHandler))
            for h in handlers
        )

    def test_rotating_file_handler(self, temp_log_dir):
        """Verifica que se use RotatingFileHandler cuando rotate_logs=True."""
        config = LogConfig(
            name="test_rotating",
            log_dir=temp_log_dir,
            console_output=False,
            file_output=True,
            rotate_logs=True
        )
        manager = LoggerManager(config)

        root_logger = logging.getLogger(config.name)
        handlers = root_logger.handlers

        rotating_handlers = [
            h for h in handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        assert len(rotating_handlers) > 0

    def test_log_exception(self, sample_log_config):
        """Verifica que log_exception funcione correctamente."""
        import io

        manager = LoggerManager(sample_log_config)
        logger = manager.get_logger("test_exceptions")

        # Agregar un handler que capture los logs
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.ERROR)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)

        try:
            raise ValueError("Test error")
        except Exception as e:
            manager.log_exception(logger, e, "Custom message")

        output = stream.getvalue()
        assert "Custom message" in output
        assert "Test error" in output

    def test_log_function_call_decorator(self, sample_log_config):
        """Verifica que el decorador log_function_call funcione."""
        manager = LoggerManager(sample_log_config)
        logger = manager.get_logger("test_decorator")

        @manager.log_function_call(logger)
        def sample_function(x, y):
            return x + y

        # Verificar que la funcion se ejecuta correctamente
        result = sample_function(2, 3)
        assert result == 5

    def test_log_function_call_with_exception(self, sample_log_config):
        """Verifica que el decorador maneje excepciones correctamente."""
        manager = LoggerManager(sample_log_config)
        logger = manager.get_logger("test_decorator_error")

        @manager.log_function_call(logger)
        def failing_function():
            raise RuntimeError("Intentional error")

        # Verificar que la excepcion se propaga
        with pytest.raises(RuntimeError):
            failing_function()

    def test_create_from_dict(self, temp_log_dir):
        """Verifica que se pueda crear LoggerManager desde un diccionario."""
        config_dict = {
            'name': 'dict_app',
            'level': LogLevel.INFO,
            'environment': Environment.PRODUCTION,
            'log_dir': str(temp_log_dir),
            'json_format': True
        }

        manager = LoggerManager.create_from_dict(config_dict)

        assert manager.config.name == 'dict_app'
        assert manager.config.level == LogLevel.INFO
        assert manager.config.environment == Environment.PRODUCTION
        assert manager.config.log_dir == temp_log_dir
        assert manager.config.json_format is True

    def test_create_from_env(self, monkeypatch, temp_log_dir):
        """Verifica que se pueda crear LoggerManager desde variables de entorno."""
        monkeypatch.setenv('LOG_NAME', 'env_app')
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
        monkeypatch.setenv('LOG_ENVIRONMENT', 'production')
        monkeypatch.setenv('LOG_DIR', str(temp_log_dir))
        monkeypatch.setenv('LOG_JSON_FORMAT', 'true')

        manager = LoggerManager.create_from_env()

        assert manager.config.name == 'env_app'
        assert manager.config.level == LogLevel.DEBUG
        assert manager.config.environment == Environment.PRODUCTION
        assert manager.config.json_format is True

    def test_log_dir_created_automatically(self, temp_log_dir):
        """Verifica que el directorio de logs se cree automáticamente."""
        log_dir = temp_log_dir / "auto_created"

        assert not log_dir.exists()

        config = LogConfig(
            name="test_auto_dir",
            log_dir=log_dir,
            file_output=True
        )
        manager = LoggerManager(config)

        assert log_dir.exists()

    def test_filters_applied(self, sample_log_config):
        """Verifica que los filtros se apliquen correctamente."""
        manager = LoggerManager(sample_log_config)

        root_logger = logging.getLogger(sample_log_config.name)
        filters = root_logger.filters

        # Debe tener al menos EnvironmentFilter
        assert len(filters) > 0

        # Si mask_sensitive=True, debe tener SensitiveDataFilter
        if sample_log_config.mask_sensitive:
            from advanced_logging.core.filters import SensitiveDataFilter
            assert any(isinstance(f, SensitiveDataFilter) for f in filters)

    def test_no_propagation(self, sample_log_config):
        """Verifica que propagate=False para evitar duplicados."""
        manager = LoggerManager(sample_log_config)

        root_logger = logging.getLogger(sample_log_config.name)

        assert root_logger.propagate is False

    def test_extra_handlers(self):
        """Verifica que se puedan agregar handlers extra."""
        mock_handler = Mock(spec=logging.Handler)

        config = LogConfig(
            name="test_extra",
            console_output=False,
            file_output=False,
            extra_handlers=[mock_handler]
        )

        manager = LoggerManager(config)

        root_logger = logging.getLogger(config.name)

        assert mock_handler in root_logger.handlers
