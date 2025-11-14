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

# Import formatters and filters
from .formatters import ColoredFormatter, JSONFormatter
from .filters import EnvironmentFilter, SensitiveDataFilter

# ============================================================================
# CONSTANTES
# ============================================================================

class LogLevel:
    """Niveles de logging disponibles."""
    DEBUG = logging.DEBUG      # 10
    INFO = logging.INFO        # 20
    WARNING = logging.WARNING  # 30
    ERROR = logging.ERROR      # 40
    CRITICAL = logging.CRITICAL # 50


class Environment:
    """Entornos de ejecución disponibles."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

@dataclass
class LogConfig:
    """
    Configuración para el sistema de logging.
    
    Attributes:
        name: Nombre del logger (usualmente el nombre del proyecto)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Entorno de ejecución
        log_dir: Directorio para archivos de log
        console_output: Si se debe mostrar en consola
        file_output: Si se debe guardar en archivo
        rotate_logs: Si se debe rotar los archivos de log
        max_bytes: Tamaño máximo por archivo (para rotación)
        backup_count: Número de backups a mantener
        json_format: Si se debe usar formato JSON
        mask_sensitive: Si se debe enmascarar datos sensibles
        django_integration: Si se debe integrar con Django
    """
    name: str = "app"
    level: int = LogLevel.INFO
    environment: str = Environment.DEVELOPMENT
    log_dir: Optional[Path] = None
    console_output: bool = True
    file_output: bool = True
    rotate_logs: bool = True
    max_bytes: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5
    json_format: bool = False
    mask_sensitive: bool = True
    django_integration: bool = False
    extra_handlers: List[logging.Handler] = field(default_factory=list)



# ============================================================================
# CLASE PRINCIPAL DE LOGGING
# ============================================================================

class LoggerManager:
    """
    Gestor centralizado de logging para aplicaciones Python/Django.
    
    Implementa el patrón Singleton para asegurar una única instancia
    del sistema de logging en toda la aplicación.
    
    Características:
        - Configuración flexible por entorno
        - Múltiples handlers (consola, archivo, rotación)
        - Formateo con colores para desarrollo
        - Formato JSON para producción
        - Filtros para datos sensibles
        - Integración con Django
        - Decoradores para logging automático
    
    Example:
        >>> config = LogConfig(
        ...     name="my_app",
        ...     level=LogLevel.DEBUG,
        ...     environment=Environment.DEVELOPMENT
        ... )
        >>> logger_manager = LoggerManager(config)
        >>> logger = logger_manager.get_logger("my_module")
        >>> logger.info("Aplicación iniciada")
    """
    
    _instances: Dict[str, 'LoggerManager'] = {}
    
    def __new__(cls, config: LogConfig):
        """
        Implementa el patrón Singleton.
        
        Args:
            config: Configuración del logger
            
        Returns:
            Instancia única de LoggerManager para cada configuración
        """
        key = f"{config.name}_{config.environment}"
        
        if key not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[key] = instance
        
        return cls._instances[key]
    
    def __init__(self, config: LogConfig):
        """
        Inicializa el gestor de logging.
        
        Args:
            config: Configuración del sistema de logging
        """
        # Evitar reinicialización en Singleton
        if hasattr(self, '_initialized'):
            return
        
        self.config = config
        self._loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
        self._initialized = True
    
    def _setup_logging(self) -> None:
        """
        Configura el sistema de logging según la configuración.
        """
        # Crear directorio de logs si no existe
        if self.config.file_output and self.config.log_dir:
            self.config.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar el logger raíz
        root_logger = logging.getLogger(self.config.name)
        root_logger.setLevel(self.config.level)
        
        # Limpiar handlers existentes
        root_logger.handlers.clear()
        
        # Agregar handlers según configuración
        if self.config.console_output:
            root_logger.addHandler(self._create_console_handler())
        
        if self.config.file_output:
            root_logger.addHandler(self._create_file_handler())
        
        # Agregar handlers personalizados
        for handler in self.config.extra_handlers:
            root_logger.addHandler(handler)
        
        # Agregar filtros
        if self.config.mask_sensitive:
            root_logger.addFilter(SensitiveDataFilter())
        
        root_logger.addFilter(EnvironmentFilter(self.config.environment))
        
        # Evitar propagación a loggers padre
        root_logger.propagate = False
    
    def _create_console_handler(self) -> logging.Handler:
        """
        Crea un handler para salida en consola.
        
        Returns:
            Handler configurado para consola
        """
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.config.level)
        
        # Formato según entorno
        if self.config.environment == Environment.DEVELOPMENT:
            # Usar colores en desarrollo
            fmt = (
                '%(levelname)s | %(asctime)s | %(name)s | '
                '%(module)s.%(funcName)s:%(lineno)d | %(message)s'
            )
            formatter = ColoredFormatter(
                fmt=fmt,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        elif self.config.json_format:
            formatter = JSONFormatter()
        else:
            fmt = (
                '%(levelname)s | %(asctime)s | %(environment)s | '
                '%(name)s | %(message)s'
            )
            formatter = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')
        
        handler.setFormatter(formatter)
        return handler
    
    def _create_file_handler(self) -> logging.Handler:
        """
        Crea un handler para salida a archivo.
        
        Returns:
            Handler configurado para archivo
        """
        if not self.config.log_dir:
            self.config.log_dir = Path('logs')
            self.config.log_dir.mkdir(exist_ok=True)
        
        log_file = self.config.log_dir / f"{self.config.name}.log"
        
        if self.config.rotate_logs:
            # Usar RotatingFileHandler
            handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
        else:
            handler = logging.FileHandler(log_file, encoding='utf-8')
        
        handler.setLevel(self.config.level)
        
        # Formato para archivo
        if self.config.json_format:
            formatter = JSONFormatter()
        else:
            fmt = (
                '%(asctime)s | %(levelname)s | %(environment)s | '
                '%(name)s | %(module)s.%(funcName)s:%(lineno)d | '
                '%(message)s'
            )
            formatter = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')
        
        handler.setFormatter(formatter)
        return handler
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Obtiene un logger configurado.
        
        Args:
            name: Nombre del logger (módulo, clase, etc.)
                  Si es None, usa el nombre de la configuración
        
        Returns:
            Logger configurado
            
        Example:
            >>> logger = logger_manager.get_logger(__name__)
            >>> logger.info("Mensaje de información")
        """
        logger_name = f"{self.config.name}.{name}" if name else self.config.name
        
        if logger_name not in self._loggers:
            logger = logging.getLogger(logger_name)
            self._loggers[logger_name] = logger
        
        return self._loggers[logger_name]
    
    def log_exception(
        self,
        logger: logging.Logger,
        exception: Exception,
        message: str = "Excepción capturada"
    ) -> None:
        """
        Registra una excepción con todo su traceback.
        
        Args:
            logger: Logger a usar
            exception: Excepción capturada
            message: Mensaje descriptivo adicional
            
        Example:
            >>> try:
            ...     risky_operation()
            ... except Exception as e:
            ...     logger_manager.log_exception(logger, e, "Error en operación")
        """
        logger.error(
            f"{message}: {str(exception)}",
            exc_info=True,
            extra={'exception_type': type(exception).__name__}
        )
    
    def log_function_call(self, logger: logging.Logger):
        """
        Decorador para logging automático de llamadas a funciones.
        
        Args:
            logger: Logger a usar
        
        Returns:
            Decorador
            
        Example:
            >>> @logger_manager.log_function_call(logger)
            ... def my_function(x, y):
            ...     return x + y
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                logger.debug(
                    f"Llamando {func.__name__} con args={args}, kwargs={kwargs}"
                )
                try:
                    result = func(*args, **kwargs)
                    logger.debug(f"{func.__name__} completado exitosamente")
                    return result
                except Exception as e:
                    logger.error(
                        f"Error en {func.__name__}: {str(e)}",
                        exc_info=True
                    )
                    raise
            return wrapper
        return decorator
    
    @staticmethod
    def create_from_dict(config_dict: Dict[str, Any]) -> 'LoggerManager':
        """
        Crea un LoggerManager desde un diccionario.
        
        Args:
            config_dict: Diccionario con configuración
        
        Returns:
            Instancia de LoggerManager
        """
        # Convertir log_dir string a Path si existe
        if 'log_dir' in config_dict and config_dict['log_dir']:
            config_dict['log_dir'] = Path(config_dict['log_dir'])
        
        config = LogConfig(**config_dict)
        return LoggerManager(config)
    
    @staticmethod
    def create_from_env() -> 'LoggerManager':
        """
        Crea un LoggerManager desde variables de entorno.
        
        Variables esperadas:
            - LOG_LEVEL: Nivel de logging (DEBUG, INFO, etc.)
            - LOG_ENVIRONMENT: Entorno (development, production, etc.)
            - LOG_DIR: Directorio para logs
            - LOG_JSON_FORMAT: true/false para formato JSON
        
        Returns:
            Instancia de LoggerManager
        """
        level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        level = getattr(LogLevel, level_str, LogLevel.INFO)
        
        config = LogConfig(
            name=os.getenv('LOG_NAME', 'app'),
            level=level,
            environment=os.getenv('LOG_ENVIRONMENT', Environment.DEVELOPMENT),
            log_dir=Path(os.getenv('LOG_DIR', 'logs')),
            json_format=os.getenv('LOG_JSON_FORMAT', 'false').lower() == 'true'
        )
        
        return LoggerManager(config)
