"""
Formateadores personalizados para logging.

Este modulo contiene formateadores especializados:
- ColoredFormatter: Salida con colores ANSI para desarrollo
- JSONFormatter: Formato JSON estructurado para produccion
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict


class ColoredFormatter(logging.Formatter):
    """
    Formateador con colores para salida en consola.

    Aplica diferentes colores segun el nivel de logging para mejorar
    la legibilidad en consola durante desarrollo.

    Attributes:
        COLORS: Diccionario con codigos ANSI para cada nivel

    Example:
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(ColoredFormatter(
        ...     '%(levelname)s | %(message)s'
        ... ))
    """

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea el registro con colores.

        Args:
            record: Registro de logging a formatear

        Returns:
            String formateado con colores ANSI
        """
        levelname = record.levelname

        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}"
                f"{self.COLORS['RESET']}"
            )

        result = super().format(record)
        record.levelname = levelname

        return result


class JSONFormatter(logging.Formatter):
    """
    Formateador que genera logs en formato JSON.

    Util para sistemas de agregacion de logs como ELK, Splunk,
    CloudWatch, Datadog, etc.

    Example:
        >>> handler = logging.FileHandler('app.log')
        >>> handler.setFormatter(JSONFormatter())
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea el registro como JSON.

        Args:
            record: Registro de logging

        Returns:
            String en formato JSON
        """
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Agregar exception si existe
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Agregar campos extra directamente al root del JSON
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # Agregar environment si existe
        if hasattr(record, 'environment'):
            log_data['environment'] = record.environment

        return json.dumps(log_data, default=str, ensure_ascii=False)
