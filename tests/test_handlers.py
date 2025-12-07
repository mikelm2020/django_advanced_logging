"""
Tests para el módulo core/handlers.py

Cubre:
- PostgreSQLConfig
- PostgreSQLHandler
"""

import logging
import queue
import time
import pytest
from unittest.mock import Mock, MagicMock, patch
from advanced_logging.core.handlers import PostgreSQLConfig, PostgreSQLHandler


class TestPostgreSQLConfig:
    """Tests para PostgreSQLConfig."""

    def test_default_config(self):
        """Verifica la configuración por defecto."""
        config = PostgreSQLConfig(host="localhost")
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "logs"
        assert config.user == "postgres"
        assert config.password == ""
        assert config.table_name == "application_logs"
        assert config.schema == "public"
        assert config.ssl_mode == "prefer"
        assert config.buffer_size == 1000
        assert config.batch_size == 10
        assert config.flush_interval == 5.0

    def test_custom_config(self):
        """Verifica que se pueda personalizar la configuración."""
        config = PostgreSQLConfig(
            host="db.example.com",
            port=5433,
            database="my_logs",
            user="logger",
            password="secret",
            table_name="custom_logs",
            schema="logging",
            buffer_size=500,
            batch_size=20
        )
        
        assert config.host == "db.example.com"
        assert config.port == 5433
        assert config.database == "my_logs"
        assert config.user == "logger"
        assert config.password == "secret"
        assert config.table_name == "custom_logs"
        assert config.schema == "logging"
        assert config.buffer_size == 500
        assert config.batch_size == 20

    def test_connection_string(self):
        """Verifica que se genere correctamente el connection string."""
        config = PostgreSQLConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass"
        )
        
        conn_str = config.connection_string
        
        assert "host=localhost" in conn_str
        assert "port=5432" in conn_str
        assert "dbname=test_db" in conn_str
        assert "user=test_user" in conn_str
        assert "password=test_pass" in conn_str
        assert "sslmode=" in conn_str


class TestPostgreSQLHandler:
    """Tests para PostgreSQLHandler."""

    @patch('advanced_logging.core.handlers.PostgreSQLHandler._connect')
    @patch('advanced_logging.core.handlers.PostgreSQLHandler._start_writer_thread')
    def test_handler_initialization(self, mock_start_thread, mock_connect, sample_postgres_config):
        """Verifica que el handler se inicialice correctamente."""
        with patch('psycopg2.connect'):
            handler = PostgreSQLHandler(sample_postgres_config)
            
            assert handler.config == sample_postgres_config
            assert isinstance(handler.log_queue, queue.Queue)
            assert handler.logs_written == 0
            assert handler.logs_failed == 0

    @patch('psycopg2.connect')
    def test_emit_adds_to_queue(self, mock_connect, sample_postgres_config):
        """Verifica que emit() agregue logs a la cola."""
        with patch.object(PostgreSQLHandler, '_start_writer_thread'):
            handler = PostgreSQLHandler(sample_postgres_config)
            
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='test.py',
                lineno=1,
                msg='Test message',
                args=(),
                exc_info=None
            )
            
            handler.emit(record)
            
            assert handler.log_queue.qsize() > 0

    @patch('psycopg2.connect')
    def test_queue_overflow_handling(self, mock_connect):
        """Verifica el manejo cuando la cola está llena."""
        config = PostgreSQLConfig(
            host="localhost",
            buffer_size=2  # Cola pequeña para forzar overflow
        )
        
        with patch.object(PostgreSQLHandler, '_start_writer_thread'):
            handler = PostgreSQLHandler(config)
            
            # Llenar la cola
            for i in range(3):
                record = logging.LogRecord(
                    name='test',
                    level=logging.INFO,
                    pathname='test.py',
                    lineno=1,
                    msg=f'Message {i}',
                    args=(),
                    exc_info=None
                )
                handler.emit(record)
            
            # La cola no debe exceder su tamaño máximo
            assert handler.log_queue.qsize() <= config.buffer_size

    @patch('psycopg2.connect')
    def test_get_statistics(self, mock_connect, sample_postgres_config):
        """Verifica que se puedan obtener estadísticas."""
        with patch.object(PostgreSQLHandler, '_start_writer_thread'):
            handler = PostgreSQLHandler(sample_postgres_config)
            handler.logs_written = 100
            handler.logs_failed = 5
            handler.connected = True
            
            stats = handler.get_statistics()
            
            assert stats['logs_written'] == 100
            assert stats['logs_failed'] == 5
            assert stats['connected'] is True
            assert 'queue_size' in stats

    @patch('psycopg2.connect')
    def test_prepare_record(self, mock_connect, sample_postgres_config):
        """Verifica que _prepare_record genere los datos correctos."""
        with patch.object(PostgreSQLHandler, '_start_writer_thread'):
            handler = PostgreSQLHandler(sample_postgres_config)
            
            record = logging.LogRecord(
                name='test.module',
                level=logging.ERROR,
                pathname='/path/to/test.py',
                lineno=42,
                msg='Error message',
                args=(),
                exc_info=None
            )
            record.module = 'test'
            record.funcName = 'test_func'
            record.thread = 12345
            record.threadName = 'MainThread'
            record.process = 9999
            
            data = handler._prepare_record(record)
            
            assert len(data) == 14  # 14 campos en la tupla
            assert data[1] == 'ERROR'  # level
            assert data[2] == 'test.module'  # logger_name
            assert data[4] == 'test'  # module
            assert data[5] == 'test_func'  # function
            assert data[6] == 42  # line_number

    @patch('psycopg2.connect')
    def test_prepare_record_with_extra_fields(self, mock_connect, sample_postgres_config):
        """Verifica que los extra_fields se serialicen correctamente."""
        with patch.object(PostgreSQLHandler, '_start_writer_thread'):
            handler = PostgreSQLHandler(sample_postgres_config)
            
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='test.py',
                lineno=1,
                msg='Test',
                args=(),
                exc_info=None
            )
            record.module = 'test'
            record.funcName = 'func'
            record.thread = 1
            record.threadName = 'MainThread'
            record.process = 1
            record.extra_fields = {
                'user_id': 123,
                'action': 'login'
            }
            
            data = handler._prepare_record(record)
            
            # extra_data debe ser JSON
            import json
            extra_data = json.loads(data[11])
            assert extra_data['user_id'] == 123
            assert extra_data['action'] == 'login'

    @patch('psycopg2.connect')
    def test_close_handler(self, mock_connect, sample_postgres_config):
        """Verifica que el handler se cierre correctamente."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        with patch.object(PostgreSQLHandler, '_start_writer_thread'):
            handler = PostgreSQLHandler(sample_postgres_config)
            handler.connection = mock_conn
            handler.running = True
            
            handler.close()
            
            assert handler.running is False
            mock_conn.close.assert_called_once()
