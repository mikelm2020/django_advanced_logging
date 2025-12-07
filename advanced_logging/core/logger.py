"""
Gestor centralizado de logging.

Este modulo contiene las clases principales:
- LogLevel: Niveles de logging
- Environment: Entornos de ejecucion
- LogConfig: Configuracion del sistema
- LoggerManager: Gestor centralizado (Singleton)
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from functools import wraps

from .formatters import ColoredFormatter, JSONFormatter
from .filters import EnvironmentFilter, SensitiveDataFilter


class LogLevel:
    """
    Niveles de logging disponibles.

    Corresponden a los niveles estandar de Python logging.

    Attributes:
        DEBUG: Informacion detallada para diagnostico (10)
        INFO: Confirmacion de que las cosas funcionan (20)
        WARNING: Indicacion de algo inesperado (30)
        ERROR: Error serio, la aplicacion no puede realizar algo (40)
        CRITICAL: Error grave, la aplicacion puede no continuar (50)
    """
    DEBUG = logging.DEBUG       # 10
    INFO = logging.INFO         # 20
    WARNING = logging.WARNING   # 30
    ERROR = logging.ERROR       # 40
    CRITICAL = logging.CRITICAL  # 50

    @classmethod
    def from_string(cls, level: str) -> int:
        """
        Convierte string a nivel de logging.

        Args:
            level: Nombre del nivel ('DEBUG', 'INFO', etc.)

        Returns:
            Valor numerico del nivel
        """
        return getattr(cls, level.upper(), cls.INFO)


class Environment:
    """
    Entornos de ejecucion disponibles.

    Attributes:
        DEVELOPMENT: Entorno de desarrollo local
        STAGING: Entorno de pruebas/staging
        PRODUCTION: Entorno de produccion
    """
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class LogConfig:
    """
    Configuracion para el sistema de logging.

    Attributes:
        name: Nombre del logger (usualmente el nombre del proyecto)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Entorno de ejecucion
        log_dir: Directorio para archivos de log
        console_output: Si se debe mostrar en consola
        file_output: Si se debe guardar en archivo
        rotate_logs: Si se debe rotar los archivos de log
        max_bytes: Tamano maximo por archivo (para rotacion)
        backup_count: Numero de backups a mantener
        json_format: Si se debe usar formato JSON
        mask_sensitive: Si se debe enmascarar datos sensibles
        extra_handlers: Lista de handlers adicionales

    Example:
        >>> config = LogConfig(
        ...     name="my_project",
        ...     level=LogLevel.DEBUG,
        ...     environment=Environment.DEVELOPMENT
        ... )
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
    extra_handlers: List[logging.Handler] = field(default_factory=list)

    def __post_init__(self):
        """Validacion y conversion post-inicializacion."""
        # Convertir level string a int si es necesario
        if isinstance(self.level, str):
            self.level = LogLevel.from_string(self.level)

        # Convertir log_dir string a Path si es necesario
        if isinstance(self.log_dir, str):
            self.log_dir = Path(self.log_dir)


class LoggerManager:
    """
    Gestor centralizado de logging para aplicaciones Django/Python.

    Implementa el patron Singleton para asegurar una unica instancia
    del sistema de logging por combinacion (name, environment).

    Caracteristicas:
        - Configuracion flexible por entorno
        - Multiples handlers (consola, archivo, rotacion)
        - Formateo con colores para desarrollo
        - Formato JSON para produccion
        - Filtros para datos sensibles
        - Decoradores para logging automatico

    Example:
        >>> config = LogConfig(
        ...     name="my_app",
        ...     level=LogLevel.DEBUG,
        ...     environment=Environment.DEVELOPMENT
        ... )
        >>> manager = LoggerManager(config)
        >>> logger = manager.get_logger("my_module")
        >>> logger.info("Aplicacion iniciada")
    """

    _instances: Dict[str, 'LoggerManager'] = {}

    def __new__(cls, config: LogConfig):
        """
        Implementa el patron Singleton.

        Args:
            config: Configuracion del logger

        Returns:
            Instancia unica de LoggerManager para cada configuracion
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
            config: Configuracion del sistema de logging
        """
        # Evitar reinicializacion en Singleton
        if hasattr(self, '_initialized'):
            return

        self.config = config
        self._loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
        self._initialized = True

    def _setup_logging(self) -> None:
        """Configura el sistema de logging segun la configuracion."""
        # Crear directorio de logs si no existe
        if self.config.file_output and self.config.log_dir:
            self.config.log_dir.mkdir(parents=True, exist_ok=True)

        # Configurar el logger raiz
        root_logger = logging.getLogger(self.config.name)
        root_logger.setLevel(self.config.level)

        # Limpiar handlers existentes
        root_logger.handlers.clear()

        # Agregar handlers segun configuracion
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

        # Evitar propagacion a loggers padre
        root_logger.propagate = False

    def _create_console_handler(self) -> logging.Handler:
        """
        Crea un handler para salida en consola.

        Returns:
            Handler configurado para consola
        """
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.config.level)

        # Formato segun entorno
        if self.config.environment == Environment.DEVELOPMENT and not self.config.json_format:
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
            name: Nombre del logger (modulo, clase, etc.)
                  Si es None, usa el nombre de la configuracion

        Returns:
            Logger configurado

        Example:
            >>> logger = manager.get_logger(__name__)
            >>> logger.info("Mensaje de informacion")
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
        message: str = "Excepcion capturada"
    ) -> None:
        """
        Registra una excepcion con todo su traceback.

        Args:
            logger: Logger a usar
            exception: Excepcion capturada
            message: Mensaje descriptivo adicional

        Example:
            >>> try:
            ...     risky_operation()
            ... except Exception as e:
            ...     manager.log_exception(logger, e, "Error en operacion")
        """
        logger.error(
            f"{message}: {str(exception)}",
            exc_info=True,
            extra={
                'extra_fields': {
                    'exception_type': type(exception).__name__
                }
            }
        )

    def log_function_call(self, logger: logging.Logger) -> Callable:
        """
        Decorador para logging automatico de llamadas a funciones.

        Args:
            logger: Logger a usar

        Returns:
            Decorador

        Example:
            >>> @manager.log_function_call(logger)
            ... def my_function(x, y):
            ...     return x + y
        """
        def decorator(func: Callable) -> Callable:
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

    def add_handler(self, handler: logging.Handler) -> None:
        """
        Agrega un handler adicional al logger raiz.

        Args:
            handler: Handler a agregar
        """
        root_logger = logging.getLogger(self.config.name)
        root_logger.addHandler(handler)

    @classmethod
    def create_from_dict(cls, config_dict: Dict[str, Any]) -> 'LoggerManager':
        """
        Crea un LoggerManager desde un diccionario.

        Args:
            config_dict: Diccionario con configuracion

        Returns:
            Instancia de LoggerManager
        """
        # Convertir log_dir string a Path si existe
        if 'log_dir' in config_dict and config_dict['log_dir']:
            config_dict['log_dir'] = Path(config_dict['log_dir'])

        config = LogConfig(**config_dict)
        return cls(config)

    @classmethod
    def create_from_env(cls) -> 'LoggerManager':
        """
        Crea un LoggerManager desde variables de entorno.

        Variables esperadas:
            - LOG_NAME: Nombre del logger
            - LOG_LEVEL: Nivel de logging (DEBUG, INFO, etc.)
            - LOG_ENVIRONMENT: Entorno (development, production, etc.)
            - LOG_DIR: Directorio para logs
            - LOG_JSON_FORMAT: true/false para formato JSON
            - LOG_CONSOLE: true/false para output en consola
            - LOG_FILE: true/false para output en archivo

        Returns:
            Instancia de LoggerManager
        """
        level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        level = LogLevel.from_string(level_str)

        log_dir = os.getenv('LOG_DIR')

        config = LogConfig(
            name=os.getenv('LOG_NAME', 'app'),
            level=level,
            environment=os.getenv('LOG_ENVIRONMENT', Environment.DEVELOPMENT),
            log_dir=Path(log_dir) if log_dir else None,
            console_output=os.getenv('LOG_CONSOLE', 'true').lower() == 'true',
            file_output=os.getenv('LOG_FILE', 'false').lower() == 'true',
            json_format=os.getenv('LOG_JSON_FORMAT', 'false').lower() == 'true'
        )

        return cls(config)

    @classmethod
    def reset_instances(cls) -> None:
        """
        Resetea todas las instancias (util para tests).
        """
        cls._instances.clear()
