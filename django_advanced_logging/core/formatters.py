import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
import traceback

# ============================================================================
# FORMATEADORES PERSONALIZADOS
# ============================================================================

class ColoredFormatter(logging.Formatter):
    """
    Formateador con colores para salida en consola.
    
    Aplica diferentes colores según el nivel de logging para mejorar
    la legibilidad en consola.
    
    Attributes:
        COLORS: Diccionario con códigos ANSI para cada nivel
    """
    
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
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
    
    Útil para sistemas de agregación de logs como ELK, Splunk, etc.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea el registro como JSON.
        
        Args:
            record: Registro de logging
            
        Returns:
            String en formato JSON
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)
