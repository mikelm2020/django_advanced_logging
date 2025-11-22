# CLAUDE.md

Guia para Claude Code cuando trabaje con este repositorio.

## Overview

Advanced Logging es una app Django auto-contenida para logging profesional. Se puede copiar y pegar en cualquier proyecto Django.

## Estructura del Proyecto

```
advanced_logging/
├── __init__.py           # Exports principales
├── apps.py               # Django AppConfig
├── models.py             # Modelo ApplicationLog
├── admin.py              # Admin para visualizar logs
├── middleware.py         # Middlewares HTTP
├── utils.py              # Funciones de utilidad
├── core/
│   ├── __init__.py
│   ├── logger.py         # LoggerManager, LogConfig, LogLevel
│   ├── handlers.py       # PostgreSQLHandler
│   ├── formatters.py     # ColoredFormatter, JSONFormatter
│   └── filters.py        # EnvironmentFilter, SensitiveDataFilter
├── migrations/
│   └── 0001_initial.py   # Migracion del modelo
├── management/
│   └── commands/
│       └── test_logging.py
└── README.md
```

## Comandos de Desarrollo

```bash
# Ejecutar tests
pytest tests/ -v

# Test con cobertura
pytest tests/ --cov=advanced_logging

# Probar logging
python manage.py test_logging
python manage.py test_logging --postgres
```

## Componentes Principales

### LoggerManager (core/logger.py)
- Patron Singleton por (name, environment)
- Configura handlers, formatters y filters
- Metodos: `get_logger()`, `log_exception()`, `log_function_call()`

### PostgreSQLHandler (core/handlers.py)
- Escritura asincrona via threading.Queue
- Batch writes configurables
- Reconexion automatica
- NO crea tablas - usa migraciones Django

### Middleware (middleware.py)
- LoggingMiddleware: Logging de requests HTTP
- ExternalIntegrationLoggingMiddleware: Logging de integraciones

### ApplicationLog (models.py)
- Modelo Django para la tabla de logs
- Indices optimizados
- Soporte JSONB para extra_data

## Configuracion

En settings.py del proyecto Django:

```python
INSTALLED_APPS = ['advanced_logging', ...]

# Opcional
ADVANCED_LOGGING = {
    'name': 'my_project',
    'level': 'DEBUG',
    'environment': 'development',
    'console_output': True,
    'file_output': False,
    'json_format': False,
    'postgres_enabled': True,
}

# Middleware opcional
MIDDLEWARE = [
    ...
    'advanced_logging.middleware.LoggingMiddleware',
]
```

## Variables de Entorno

- LOG_NAME, LOG_LEVEL, LOG_ENVIRONMENT
- LOG_CONSOLE, LOG_FILE, LOG_JSON
- POSTGRES_ENABLED, LOG_DB_HOST, LOG_DB_PORT, LOG_DB_NAME, LOG_DB_USER, LOG_DB_PASSWORD

## Uso Basico

```python
from advanced_logging import get_logger

logger = get_logger(__name__)
logger.info("Mensaje", extra={'extra_fields': {'key': 'value'}})
```

## Testing

Los tests estan en `tests/` y usan pytest-django con SQLite en memoria.

```bash
pytest tests/ -v --tb=short
```

## Notas Importantes

1. La app es auto-contenida - solo copiar la carpeta
2. No es un paquete instalable via pip/poetry
3. La tabla se crea con `python manage.py migrate`
4. PostgreSQLHandler requiere psycopg2-binary o psycopg
