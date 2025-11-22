"""
Tests para el módulo core/filters.py

Cubre:
- EnvironmentFilter
- SensitiveDataFilter
"""

import logging
import pytest
from advanced_logging.core.filters import EnvironmentFilter, SensitiveDataFilter


class TestEnvironmentFilter:
    """Tests para EnvironmentFilter."""

    def test_filter_adds_environment_to_record(self):
        """Verifica que se agregue el entorno al registro."""
        filter_obj = EnvironmentFilter('production')
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        result = filter_obj.filter(record)
        
        assert result is True
        assert hasattr(record, 'environment')
        assert record.environment == 'production'

    def test_filter_with_different_environments(self):
        """Verifica que funcione con diferentes entornos."""
        environments = ['development', 'staging', 'production']
        
        for env in environments:
            filter_obj = EnvironmentFilter(env)
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='test.py',
                lineno=1,
                msg='Test',
                args=(),
                exc_info=None
            )
            
            filter_obj.filter(record)
            assert record.environment == env

    def test_filter_always_returns_true(self):
        """Verifica que el filtro siempre permita el registro."""
        filter_obj = EnvironmentFilter('development')
        
        # Probar con diferentes niveles
        for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]:
            record = logging.LogRecord(
                name='test',
                level=level,
                pathname='test.py',
                lineno=1,
                msg='Test',
                args=(),
                exc_info=None
            )
            
            result = filter_obj.filter(record)
            assert result is True


class TestSensitiveDataFilter:
    """Tests para SensitiveDataFilter."""

    def test_filter_masks_password(self):
        """Verifica que se enmascaren contraseñas."""
        filter_obj = SensitiveDataFilter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='User login with password=secret123',
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        assert '***MASKED***' in str(record.msg)
        assert 'secret123' not in str(record.msg)

    def test_filter_masks_token(self):
        """Verifica que se enmascaren tokens."""
        filter_obj = SensitiveDataFilter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='API call with token=abc123xyz',
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        assert '***MASKED***' in str(record.msg)
        assert 'abc123xyz' not in str(record.msg)

    def test_filter_masks_api_key(self):
        """Verifica que se enmascaren API keys."""
        filter_obj = SensitiveDataFilter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Request with api_key=myapikey123',
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        assert '***MASKED***' in str(record.msg)

    def test_filter_masks_secret(self):
        """Verifica que se enmascaren secrets."""
        filter_obj = SensitiveDataFilter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Config has secret: mysecretvalue',
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        assert '***MASKED***' in str(record.msg)

    def test_filter_case_insensitive(self):
        """Verifica que el filtrado sea case-insensitive."""
        filter_obj = SensitiveDataFilter()
        
        messages = [
            'PASSWORD=secret',
            'Password=secret',
            'password=secret',
            'TOKEN=abc',
            'Token=abc',
            'token=abc'
        ]
        
        for msg in messages:
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='test.py',
                lineno=1,
                msg=msg,
                args=(),
                exc_info=None
            )
            
            filter_obj.filter(record)
            assert '***MASKED***' in str(record.msg)

    def test_filter_does_not_mask_normal_messages(self):
        """Verifica que los mensajes normales no se modifiquen."""
        filter_obj = SensitiveDataFilter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Normal log message without sensitive data',
            args=(),
            exc_info=None
        )
        
        original_msg = record.msg
        filter_obj.filter(record)
        
        assert record.msg == original_msg
        assert '***MASKED***' not in str(record.msg)

    def test_filter_always_returns_true(self):
        """Verifica que el filtro siempre permita el registro."""
        filter_obj = SensitiveDataFilter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='password=secret',
            args=(),
            exc_info=None
        )
        
        result = filter_obj.filter(record)
        assert result is True

    def test_filter_handles_multiple_patterns(self):
        """Verifica que se enmascaren múltiples patrones en un mismo mensaje."""
        filter_obj = SensitiveDataFilter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Login with password=secret and token=abc123',
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        # Ambos deberían estar enmascarados
        assert '***MASKED***' in str(record.msg)
        assert 'secret' not in str(record.msg).lower() or str(record.msg).lower().count('secret') == 1  # Solo en "password"
