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
# FILTROS PERSONALIZADOS
# ============================================================================

class EnvironmentFilter(logging.Filter):
    """
    Filtro que agrega información del entorno a los logs.
    
    Attributes:
        environment: Entorno actual de ejecución
    """
    
    def __init__(self, environment: str):
        """
        Inicializa el filtro.
        
        Args:
            environment: Nombre del entorno (development, production, etc.)
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
    
    Reemplaza información sensible como passwords, tokens, etc.
    """
    
    SENSITIVE_PATTERNS = [
        'password', 'token', 'secret', 'api_key',
        'access_key', 'private_key', 'credential'
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filtra datos sensibles del mensaje.
        
        Args:
            record: Registro de logging
            
        Returns:
            True (siempre permite el registro)
        """
        message = record.getMessage().lower()
        
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                record.msg = self._mask_sensitive_data(str(record.msg))
        
        return True
    
    def _mask_sensitive_data(self, text: str) -> str:
        """
        Enmascara datos sensibles en el texto.
        
        Args:
            text: Texto a enmascarar
            
        Returns:
            Texto con datos sensibles enmascarados
        """
        import re
        
        for pattern in self.SENSITIVE_PATTERNS:
            regex = rf"({pattern}['\"]?\s*[:=]\s*['\"]?)([^'\",\s]+)"
            text = re.sub(regex, r"\1***MASKED***", text, flags=re.IGNORECASE)
        
        return text
