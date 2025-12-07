"""
Configuracion de pytest para advanced_logging.

Este modulo contiene fixtures compartidas por todos los tests.
"""

import os
import tempfile
import shutil
import logging
from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock

# Configurar Django antes de importar cualquier cosa de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')

import django
django.setup()


@pytest.fixture
def temp_log_dir():
    """Crea un directorio temporal para logs durante el test."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def clean_logger_state():
    """Limpia el estado de los loggers entre tests."""
    # Guardar estado original
    original_loggers = logging.Logger.manager.loggerDict.copy()

    yield

    # Restaurar estado
    logging.Logger.manager.loggerDict = original_loggers

    # Limpiar handlers de root logger
    root = logging.getLogger()
    root.handlers = []


@pytest.fixture
def mock_postgres_connection():
    """Mock de conexion PostgreSQL."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = None
    return mock_conn


@pytest.fixture
def mock_psycopg2(monkeypatch, mock_postgres_connection):
    """Mock del modulo psycopg2."""
    mock_module = MagicMock()
    mock_module.connect.return_value = mock_postgres_connection

    # Mock de psycopg2
    monkeypatch.setattr('psycopg2.connect', mock_module.connect)

    return mock_module


@pytest.fixture
def sample_log_config():
    """Configuracion de log de ejemplo para tests."""
    from advanced_logging import LogConfig, LogLevel, Environment

    return LogConfig(
        name="test_app",
        level=LogLevel.DEBUG,
        environment=Environment.DEVELOPMENT,
        console_output=True,
        file_output=False,
        mask_sensitive=True
    )


@pytest.fixture
def sample_postgres_config():
    """Configuracion de PostgreSQL de ejemplo para tests."""
    from advanced_logging import PostgreSQLConfig

    return PostgreSQLConfig(
        host="localhost",
        port=5432,
        database="test_logs",
        user="test_user",
        password="test_password",
        table_name="test_application_logs"
    )


@pytest.fixture
def django_request_factory():
    """Factory para crear requests de Django."""
    from django.test import RequestFactory
    return RequestFactory()


@pytest.fixture
def django_user():
    """Usuario de Django para tests."""
    from django.contrib.auth.models import User

    user = User(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )
    # No guardamos en BD para tests rapidos
    user.id = 1
    return user


@pytest.fixture(autouse=True)
def reset_logger_manager():
    """Resetea el LoggerManager singleton entre tests."""
    from advanced_logging.core.logger import LoggerManager

    # Limpiar instancias singleton
    LoggerManager._instances.clear()

    yield

    # Limpiar despues del test
    LoggerManager._instances.clear()


@pytest.fixture(autouse=True)
def reset_global_logger_manager():
    """Resetea el logger manager global en utils."""
    from advanced_logging import utils

    # Guardar estado original
    original_manager = utils._logger_manager

    yield

    # Restaurar
    utils._logger_manager = original_manager
