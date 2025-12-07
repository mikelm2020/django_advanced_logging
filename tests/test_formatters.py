"""
Tests para el módulo core/formatters.py

Cubre:
- ColoredFormatter
- JSONFormatter
"""

import logging
import json
import pytest
from advanced_logging.core.formatters import ColoredFormatter, JSONFormatter


class TestColoredFormatter:
    """Tests para ColoredFormatter."""

    def test_formatter_creates_colored_output(self):
        """Verifica que se agreguen colores ANSI a los logs."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=1,
            msg='Error message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Debe contener códigos ANSI de color
        assert '\033[' in formatted
        assert 'Error message' in formatted

    def test_different_colors_for_different_levels(self):
        """Verifica que diferentes niveles tengan diferentes colores."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')
        
        levels = [
            (logging.DEBUG, 'DEBUG'),
            (logging.INFO, 'INFO'),
            (logging.WARNING, 'WARNING'),
            (logging.ERROR, 'ERROR'),
            (logging.CRITICAL, 'CRITICAL'),
        ]
        
        formatted_messages = []
        for level, name in levels:
            record = logging.LogRecord(
                name='test',
                level=level,
                pathname='test.py',
                lineno=1,
                msg=f'{name} message',
                args=(),
                exc_info=None
            )
            formatted_messages.append(formatter.format(record))
        
        # Todos deben tener códigos ANSI
        assert all('\033[' in msg for msg in formatted_messages)
        
        # Deben ser diferentes entre sí
        assert len(set(formatted_messages)) == len(formatted_messages)

    def test_levelname_preserved(self):
        """Verifica que el levelname original se preserve después del formateo."""
        formatter = ColoredFormatter('%(levelname)s')
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test',
            args=(),
            exc_info=None
        )
        
        original_levelname = record.levelname
        formatter.format(record)
        
        # Después del formateo, levelname debe volver a su valor original
        assert record.levelname == original_levelname


class TestJSONFormatter:
    """Tests para JSONFormatter."""

    def test_formatter_creates_valid_json(self):
        """Verifica que se genere JSON válido."""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name='test.module',
            level=logging.INFO,
            pathname='/path/to/test.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None
        )
        record.module = 'test'
        record.funcName = 'test_func'
        
        formatted = formatter.format(record)
        
        # Debe ser JSON válido
        data = json.loads(formatted)
        
        assert isinstance(data, dict)
        assert data['message'] == 'Test message'
        assert data['level'] == 'INFO'
        assert data['logger'] == 'test.module'
        assert data['module'] == 'test'
        assert data['function'] == 'test_func'
        assert data['line'] == 42

    def test_json_contains_timestamp(self):
        """Verifica que el JSON contenga timestamp."""
        formatter = JSONFormatter()
        
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
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert 'timestamp' in data
        # Timestamp debe estar en formato ISO
        assert 'T' in data['timestamp']

    def test_json_with_exception(self):
        """Verifica que las excepciones se incluyan en el JSON."""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test exception")
        except Exception:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name='test',
            level=logging.ERROR,
            pathname='test.py',
            lineno=1,
            msg='Error occurred',
            args=(),
            exc_info=exc_info
        )
        record.module = 'test'
        record.funcName = 'func'
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert 'exception' in data
        assert 'ValueError' in data['exception']
        assert 'Test exception' in data['exception']

    def test_json_with_extra_fields(self):
        """Verifica que los campos extra se incluyan en el JSON."""
        formatter = JSONFormatter()
        
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
        record.extra_fields = {
            'user_id': 123,
            'action': 'login',
            'ip_address': '192.168.1.1'
        }
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert data['user_id'] == 123
        assert data['action'] == 'login'
        assert data['ip_address'] == '192.168.1.1'
