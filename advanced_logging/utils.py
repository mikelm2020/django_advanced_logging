"""
Utilidades para Advanced Logging.

Este modulo proporciona funciones helper para configurar y usar
el sistema de logging de forma simple.
"""

import os
import logging
from typing import Optional
from functools import wraps
from pathlib import Path

from .core.logger import LoggerManager, LogConfig, LogLevel, Environment
from .core.handlers import PostgreSQLHandler, PostgreSQLConfig


# Variable global para el gestor de logging
_logger_manager: Optional[LoggerManager] = None


def initialize_logging(
    config: Optional[LogConfig] = None,
    **kwargs
) -> LoggerManager:
    """
    Inicializa el sistema de logging.

    Args:
        config: Objeto LogConfig o None para usar valores por defecto
        **kwargs: Argumentos para crear LogConfig si config es None

    Returns:
        Instancia de LoggerManager

    Example:
        >>> # Usando LogConfig
        >>> from advanced_logging import LogConfig, initialize_logging
        >>> config = LogConfig(name="my_app", level="DEBUG")
        >>> initialize_logging(config)

        >>> # Usando kwargs
        >>> initialize_logging(name="my_app", level="DEBUG")

        >>> # Desde variables de entorno
        >>> initialize_logging()
    """
    global _logger_manager

    if config is None:
        if kwargs:
            # Manejar configuracion de postgres si viene en kwargs
            postgres_config = kwargs.pop('postgres_config', None)
            postgres_enabled = kwargs.pop('postgres_enabled', False)

            # Convertir level string a int si es necesario
            if 'level' in kwargs and isinstance(kwargs['level'], str):
                kwargs['level'] = LogLevel.from_string(kwargs['level'])

            config = LogConfig(**kwargs)

            # Agregar handler de PostgreSQL si esta habilitado
            if postgres_enabled and postgres_config:
                pg_config = PostgreSQLConfig(**postgres_config)
                pg_handler = PostgreSQLHandler(pg_config)
                pg_handler.setLevel(config.level)
                config.extra_handlers.append(pg_handler)
        else:
            # Crear desde variables de entorno
            return initialize_from_env()

    _logger_manager = LoggerManager(config)
    return _logger_manager


def initialize_from_env() -> LoggerManager:
    """
    Inicializa el logging desde variables de entorno.

    Variables de entorno:
        LOG_NAME: Nombre del logger (default: "app")
        LOG_LEVEL: Nivel de logging (default: "INFO")
        LOG_ENVIRONMENT: Entorno (development/staging/production)
        LOG_DIR: Directorio para logs
        LOG_CONSOLE: "true"/"false" para output en consola
        LOG_FILE: "true"/"false" para output en archivo
        LOG_JSON: "true"/"false" para formato JSON
        POSTGRES_ENABLED: "true"/"false" para habilitar PostgreSQL
        LOG_DB_HOST: Host de PostgreSQL
        LOG_DB_PORT: Puerto de PostgreSQL
        LOG_DB_NAME: Nombre de base de datos
        LOG_DB_USER: Usuario de PostgreSQL
        LOG_DB_PASSWORD: Contrasena de PostgreSQL

    Returns:
        Instancia de LoggerManager

    Example:
        >>> import os
        >>> os.environ['LOG_LEVEL'] = 'DEBUG'
        >>> manager = initialize_from_env()
    """
    global _logger_manager

    # Nivel de logging
    level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    level = LogLevel.from_string(level_str)

    # Directorio de logs
    log_dir = os.getenv('LOG_DIR')

    config = LogConfig(
        name=os.getenv('LOG_NAME', 'app'),
        level=level,
        environment=os.getenv('LOG_ENVIRONMENT', Environment.DEVELOPMENT),
        log_dir=Path(log_dir) if log_dir else None,
        console_output=os.getenv('LOG_CONSOLE', 'true').lower() == 'true',
        file_output=os.getenv('LOG_FILE', 'false').lower() == 'true',
        json_format=os.getenv('LOG_JSON', 'false').lower() == 'true',
    )

    # PostgreSQL
    postgres_enabled = os.getenv('POSTGRES_ENABLED', 'false').lower() == 'true'

    if postgres_enabled:
        pg_config = PostgreSQLConfig(
            host=os.getenv('LOG_DB_HOST', 'localhost'),
            port=int(os.getenv('LOG_DB_PORT', '5432')),
            database=os.getenv('LOG_DB_NAME', 'logs'),
            user=os.getenv('LOG_DB_USER', 'postgres'),
            password=os.getenv('LOG_DB_PASSWORD', ''),
            table_name=os.getenv(
                'LOG_DB_TABLE',
                'advanced_logging_applicationlog'
            ),
        )
        pg_handler = PostgreSQLHandler(pg_config)
        pg_handler.setLevel(level)
        config.extra_handlers.append(pg_handler)

    _logger_manager = LoggerManager(config)
    return _logger_manager


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Obtiene un logger configurado.

    Si el sistema no esta inicializado, lo inicializa automaticamente
    con configuracion por defecto o desde variables de entorno.

    Args:
        name: Nombre del logger (modulo/componente)

    Returns:
        Logger configurado

    Example:
        >>> from advanced_logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello world!")

        >>> # En un modulo especifico
        >>> logger = get_logger('my_app.users')
        >>> logger.debug("User created")
    """
    global _logger_manager

    if _logger_manager is None:
        initialize_from_env()

    return _logger_manager.get_logger(name)


def get_logger_manager() -> Optional[LoggerManager]:
    """
    Obtiene la instancia global del LoggerManager.

    Returns:
        LoggerManager o None si no esta inicializado

    Example:
        >>> manager = get_logger_manager()
        >>> if manager:
        ...     print("Logging inicializado")
    """
    return _logger_manager


def reset_logging() -> None:
    """
    Resetea el sistema de logging (util para tests).

    Example:
        >>> from advanced_logging import reset_logging
        >>> reset_logging()
        >>> # Ahora puedes inicializar con nueva configuracion
    """
    global _logger_manager
    _logger_manager = None
    LoggerManager.reset_instances()


def log_execution(
    logger_name: Optional[str] = None,
    level: str = "DEBUG"
):
    """
    Decorador para logging automatico de ejecucion de funciones.

    Args:
        logger_name: Nombre del logger a usar (None para auto)
        level: Nivel de logging ("DEBUG", "INFO", etc.)

    Returns:
        Decorador

    Example:
        >>> from advanced_logging import log_execution
        >>>
        >>> @log_execution()
        ... def my_function(x, y):
        ...     return x + y
        >>>
        >>> @log_execution(logger_name="my_app.math", level="INFO")
        ... def complex_calculation(data):
        ...     return sum(data)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener logger
            name = logger_name or func.__module__
            logger = get_logger(name)

            # Nivel de logging
            log_method = getattr(logger, level.lower())

            # Log entrada
            log_method(
                f"Ejecutando {func.__name__}",
                extra={
                    'extra_fields': {
                        'function': func.__name__,
                        'module': func.__module__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                }
            )

            try:
                import time
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                log_method(
                    f"{func.__name__} completado en {duration:.3f}s",
                    extra={
                        'extra_fields': {
                            'function': func.__name__,
                            'duration_seconds': round(duration, 3)
                        }
                    }
                )
                return result

            except Exception as e:
                logger.error(
                    f"Error en {func.__name__}: {str(e)}",
                    exc_info=True,
                    extra={
                        'extra_fields': {
                            'function': func.__name__,
                            'exception_type': type(e).__name__
                        }
                    }
                )
                raise

        return wrapper

    return decorator
