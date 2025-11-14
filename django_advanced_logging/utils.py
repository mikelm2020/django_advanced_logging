# utils.py

"""
Utilidades para facilitar el uso del sistema de logging.

Este módulo proporciona funciones helper para configurar y usar
el sistema de logging de forma simple.
"""

from typing import Optional
from .core.logger import LoggerManager, LogConfig
from .core.handlers import PostgreSQLConfig
import logging
import os


# Variable global para el gestor de logging
_logger_manager: Optional[LoggerManager] = None


def initialize_logging(config: Optional[LogConfig] = None, **kwargs) -> LoggerManager:
    """
    Inicializa el sistema de logging.
    
    Args:
        config: Objeto LogConfig o None para usar valores por defecto
        **kwargs: Argumentos para crear LogConfig si config es None
    
    Returns:
        Instancia de LoggerManager
    
    Example:
        >>> # Usando LogConfig
        >>> from django_advanced_logging import LogConfig, initialize_logging
        >>> config = LogConfig(name="my_app", level="DEBUG")
        >>> initialize_logging(config)
        
        >>> # Usando kwargs
        >>> initialize_logging(name="my_app", level="DEBUG")
        
        >>> # Desde variables de entorno
        >>> initialize_logging()  # Lee variables de entorno
    """
    global _logger_manager
    
    if config is None:
        if kwargs:
            # Crear config desde kwargs
            config = LogConfig(**kwargs)
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
        LOG_DB_PASSWORD: Contraseña de PostgreSQL
        LOG_DB_TABLE: Nombre de tabla para logs
    
    Returns:
        Instancia de LoggerManager
    
    Example:
        >>> import os
        >>> os.environ['LOG_LEVEL'] = 'DEBUG'
        >>> os.environ['POSTGRES_ENABLED'] = 'true'
        >>> manager = initialize_from_env()
    """
    global _logger_manager
    
    from pathlib import Path
    from .core.logger import LogLevel, Environment
    
    # Nivel de logging
    level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    level = getattr(LogLevel, level_str, LogLevel.INFO)
    
    # PostgreSQL
    postgres_enabled = os.getenv('POSTGRES_ENABLED', 'false').lower() == 'true'
    postgres_config = None
    
    if postgres_enabled:
        postgres_config = PostgreSQLConfig(
            host=os.getenv('LOG_DB_HOST', 'localhost'),
            port=int(os.getenv('LOG_DB_PORT', '5432')),
            database=os.getenv('LOG_DB_NAME', 'logs'),
            user=os.getenv('LOG_DB_USER', 'postgres'),
            password=os.getenv('LOG_DB_PASSWORD', ''),
            table_name=os.getenv('LOG_DB_TABLE', 'application_logs')
        )
    
    config = LogConfig(
        name=os.getenv('LOG_NAME', 'app'),
        level=level,
        environment=os.getenv('LOG_ENVIRONMENT', Environment.DEVELOPMENT),
        log_dir=Path(os.getenv('LOG_DIR', 'logs')) if os.getenv('LOG_DIR') else None,
        console_output=os.getenv('LOG_CONSOLE', 'true').lower() == 'true',
        file_output=os.getenv('LOG_FILE', 'true').lower() == 'true',
        json_format=os.getenv('LOG_JSON', 'false').lower() == 'true',
        postgres_enabled=postgres_enabled,
        postgres_config=postgres_config
    )
    
    _logger_manager = LoggerManager(config)
    return _logger_manager


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Obtiene un logger configurado.
    
    Si el sistema no está inicializado, lo inicializa automáticamente
    con configuración por defecto o desde variables de entorno.
    
    Args:
        name: Nombre del logger (módulo/componente)
    
    Returns:
        Logger configurado
    
    Example:
        >>> from django_advanced_logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello world!")
        
        >>> # En un módulo específico
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
        LoggerManager o None si no está inicializado
    
    Example:
        >>> from django_advanced_logging import get_logger_manager
        >>> manager = get_logger_manager()
        >>> if manager:
        ...     stats = manager.get_postgres_statistics()
        ...     print(stats)
    """
    return _logger_manager


def reset_logging() -> None:
    """
    Resetea el sistema de logging (útil para tests).
    
    Example:
        >>> from django_advanced_logging import reset_logging
        >>> reset_logging()
        >>> # Ahora puedes inicializar con nueva configuración
    """
    global _logger_manager
    _logger_manager = None


# Decorator helper
def log_execution(logger_name: Optional[str] = None, level: str = "DEBUG"):
    """
    Decorador para logging automático de ejecución de funciones.
    
    Args:
        logger_name: Nombre del logger a usar (None para auto)
        level: Nivel de logging ("DEBUG", "INFO", etc.)
    
    Returns:
        Decorador
    
    Example:
        >>> from django_advanced_logging import log_execution
        >>> 
        >>> @log_execution()
        ... def my_function(x, y):
        ...     return x + y
        >>> 
        >>> @log_execution(logger_name="my_app.math", level="INFO")
        ... def complex_calculation(data):
        ...     return sum(data)
    """
    from functools import wraps
    
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
                result = func(*args, **kwargs)
                log_method(f"{func.__name__} completado exitosamente")
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


def configure_django_logging(
    django_settings_module,
    config: Optional[LogConfig] = None,
    **kwargs
) -> LoggerManager:
    """
    Configura el logging para un proyecto Django.
    
    Esta función lee la configuración de Django settings y configura
    el sistema de logging automáticamente.
    
    Args:
        django_settings_module: Módulo de settings de Django
        config: LogConfig opcional
        **kwargs: Argumentos adicionales para LogConfig
    
    Returns:
        LoggerManager configurado
    
    Example:
        >>> from django.conf import settings
        >>> from django_advanced_logging import configure_django_logging
        >>> 
        >>> manager = configure_django_logging(settings)
    """
    from pathlib import Path
    
    # Si no hay config, crearla desde Django settings
    if config is None:
        # Obtener configuración desde Django settings
        logging_config = getattr(
            django_settings_module, 
            'LOGGING_CONFIG', 
            {}
        )
        
        # Mezclar con kwargs
        logging_config.update(kwargs)
        
        # Usar base_dir de Django si está disponible
        if not logging_config.get('log_dir') and hasattr(django_settings_module, 'BASE_DIR'):
            logging_config['log_dir'] = Path(django_settings_module.BASE_DIR) / 'logs'
        
        config = LogConfig(**logging_config)
    
    return initialize_logging(config)
