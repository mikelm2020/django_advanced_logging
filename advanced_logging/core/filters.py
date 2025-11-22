"""
Filtros personalizados para logging.

Este modulo contiene filtros especializados:
- EnvironmentFilter: Agrega informacion del entorno
- SensitiveDataFilter: Enmascara datos sensibles
"""

import logging
import re
from typing import List


class EnvironmentFilter(logging.Filter):
    """
    Filtro que agrega informacion del entorno a los logs.

    Inyecta el atributo 'environment' en cada registro de log,
    permitiendo identificar el entorno de ejecucion.

    Attributes:
        environment: Entorno actual de ejecucion

    Example:
        >>> logger.addFilter(EnvironmentFilter('production'))
    """

    def __init__(self, environment: str):
        """
        Inicializa el filtro.

        Args:
            environment: Nombre del entorno (development, staging, production)
        """
        super().__init__()
        self.environment = environment

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Agrega el entorno al registro.

        Args:
            record: Registro de logging

        Returns:
            True (siempre permite el registro)
        """
        record.environment = self.environment
        return True


class SensitiveDataFilter(logging.Filter):
    """
    Filtro que oculta datos sensibles en los logs.

    Reemplaza automaticamente informacion sensible como passwords,
    tokens, API keys, etc. con '***MASKED***'.

    Attributes:
        SENSITIVE_PATTERNS: Lista de patrones a enmascarar

    Example:
        >>> logger.addFilter(SensitiveDataFilter())
        >>> logger.info("password=secret123")  # -> "password=***MASKED***"
    """

    SENSITIVE_PATTERNS: List[str] = [
        'password',
        'passwd',
        'pwd',
        'token',
        'secret',
        'api_key',
        'apikey',
        'access_key',
        'private_key',
        'credential',
        'auth',
        'bearer',
        'authorization',
    ]

    def __init__(self, additional_patterns: List[str] = None):
        """
        Inicializa el filtro.

        Args:
            additional_patterns: Patrones adicionales a enmascarar
        """
        super().__init__()
        if additional_patterns:
            self.SENSITIVE_PATTERNS = self.SENSITIVE_PATTERNS + additional_patterns

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filtra datos sensibles del mensaje.

        Args:
            record: Registro de logging

        Returns:
            True (siempre permite el registro)
        """
        if record.msg:
            message = str(record.msg).lower()

            for pattern in self.SENSITIVE_PATTERNS:
                if pattern in message:
                    record.msg = self._mask_sensitive_data(str(record.msg))
                    break

        return True

    def _mask_sensitive_data(self, text: str) -> str:
        """
        Enmascara datos sensibles en el texto.

        Args:
            text: Texto a enmascarar

        Returns:
            Texto con datos sensibles enmascarados
        """
        for pattern in self.SENSITIVE_PATTERNS:
            # Patron para key=value, key:value, key="value", etc.
            regex = rf"({pattern}['\"]?\s*[:=]\s*['\"]?)([^'\",\s}}]+)"
            text = re.sub(regex, r"\1***MASKED***", text, flags=re.IGNORECASE)

        return text
