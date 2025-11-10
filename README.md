
[![PyPI version](https://badge.fury.io/py/django-advanced-logging.svg)](https://badge.fury.io/py/django-advanced-logging)
[![Python versions](https://img.shields.io/pypi/pyversions/django-advanced-logging.svg)](https://pypi.org/project/django-advanced-logging/)
[![Django versions](https://img.shields.io/pypi/djversions/django-advanced-logging.svg)](https://pypi.org/project/django-advanced-logging/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Sistema de logging profesional y escalable para proyectos Python y Django con soporte para PostgreSQL, múltiples handlers, formateo avanzado y logging asíncrono.

## ✨ Características

- 🚀 **Logging asíncrono a PostgreSQL** - No bloquea tu aplicación
- 🎨 **Formateo con colores** - Mejor legibilidad en desarrollo
- 📊 **Campos personalizados (JSONB)** - Búsquedas avanzadas en PostgreSQL
- 🔍 **Filtros de datos sensibles** - Enmascara passwords y tokens automáticamente
- 🌍 **Multi-entorno** - Configuración diferente para dev/staging/production
- 🔄 **Rotación de logs** - Gestión automática de archivos
- 🐍 **Compatible con Django** - Flexible para cualquier proyecto
- ⚡ **Zero-config para Django** - Solo agregar a INSTALLED_APPS
- 🎯 **Thread-safe** - Seguro para aplicaciones concurrentes
- 📦 **Middleware incluido** - Logging automático de requests HTTP

## 📦 Instalación

 ⚠️ **USO INTERNO** - Este paquete es para uso exclusivo de [Tu Empresa]

## Instalación

```bash
# Desde repositorio Git privado
pip install git+https://github.com/tu-empresa/django-advanced-logging.git@v1.0.0

# O con Poetry
poetry add git+https://github.com/tu-empresa/django-advanced-logging.git#v1.0.0


## 🚀 Inicio Rápido

### Uso Básico (Python puro)

```python
from django_advanced_logging import get_logger

# Obtener un logger
logger = get_logger(__name__)

# Usar el logger
logger.info("¡Hola mundo!")
logger.debug("Mensaje de debug")
logger.warning("Advertencia")
logger.error("Error")

# Con campos personalizados
logger.info(
    "Usuario creado",
    extra={
        'extra_fields': {
            'user_id': 123,
            'username': 'john',
            'email': 'john@example.com'
        }
    }
)
```

### Uso con Django

#### 1. Agregar a INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... otras apps
    'django_advanced_logging',
]
```

#### 2. Configurar el logging

```python
# settings.py

# Configuración básica
LOGGING_CONFIG = {
    'name': 'mi_proyecto',
    'level': 'INFO',
    'environment': 'development',
    'console_output': True,
    'file_output': True,
}

# Configuración completa con PostgreSQL
LOGGING_CONFIG = {
    'name': 'mi_proyecto',
    'level': 'DEBUG',
    'environment': 'development',
    'log_dir': BASE_DIR / 'logs',
    'console_output': True,
    'file_output': True,
    'rotate_logs': True,
    'json_format': False,  # True para producción
    'postgres_enabled': True,
    'postgres_config': {
        'host': 'localhost',
        'port': 5432,
        'database': 'mi_base_datos',
        'user': 'postgres',
        'password': 'password',
        'table_name': 'application_logs',
    }
}
```

#### 3. Agregar el Middleware (opcional)

```python
# settings.py
MIDDLEWARE = [
    # ... otros middleware
    'django_advanced_logging.django.middleware.LoggingMiddleware',
]
```

#### 4. Usar en tus views y modelos

```python
from django_advanced_logging import get_logger

logger = get_logger(__name__)

def my_view(request):
    logger.info(
        f"Usuario {request.user} accedió a la vista",
        extra={
            'extra_fields': {
                'user_id': request.user.id,
                'path': request.path,
                'method': request.method
            }
        }
    )
    # ... tu código
```

## 🎯 Ejemplos Avanzados

### Decorador para logging automático

```python
from django_advanced_logging import log_execution, get_logger

logger = get_logger(__name__)

@log_execution(logger_name='my_app.services', level='INFO')
def proceso_complejo(datos):
    """Esta función será loggeada automáticamente."""
    return sum(datos)

resultado = proceso_complejo([1, 2, 3, 4, 5])
```

### Uso del LoggerManager directamente

```python
from django_advanced_logging import LoggerManager, LogConfig, PostgreSQLConfig

# Configuración personalizada
config = LogConfig(
    name='mi_app',
    level='DEBUG',
    environment='production',
    postgres_enabled=True,
    postgres_config=PostgreSQLConfig(
        host='localhost',
        database='logs_db',
        user='logger',
        password='secret'
    )
)

# Crear el manager
manager = LoggerManager(config)

# Obtener logger
logger = manager.get_logger('mi_modulo')
logger.info("Mensaje")

# Ver estadísticas de PostgreSQL
stats = manager.get_postgres_statistics()
print(f"Logs escritos: {stats['logs_written']}")
print(f"Logs fallidos: {stats['logs_failed']}")
```

### Configuración desde variables de entorno

```python
# En tu código
from django_advanced_logging import initialize_from_env, get_logger

# Inicializa desde .env
initialize_from_env()

# Usa el logger
logger = get_logger(__name__)
logger.info("Configurado desde variables de entorno")
```

```bash
# .env
LOG_NAME=mi_app
LOG_LEVEL=DEBUG
LOG_ENVIRONMENT=development
LOG_DIR=logs
POSTGRES_ENABLED=true
LOG_DB_HOST=localhost
LOG_DB_PORT=5432
LOG_DB_NAME=mi_base_datos
LOG_DB_USER=postgres
LOG_DB_PASSWORD=secret
LOG_DB_TABLE=application_logs
```

## 📊 Consultar Logs en PostgreSQL

```sql
-- Ver todos los logs recientes
SELECT * FROM application_logs 
ORDER BY timestamp DESC 
LIMIT 100;

-- Logs por nivel
SELECT level, COUNT(*) 
FROM application_logs 
GROUP BY level;

-- Buscar en campos personalizados (JSONB)
SELECT * FROM application_logs 
WHERE extra_data->>'user_id' = '123';

-- Logs con errores de las últimas 24 horas
SELECT * FROM application_logs 
WHERE level IN ('ERROR', 'CRITICAL')
  AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Estadísticas por hora
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    level,
    COUNT(*) as count
FROM application_logs 
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY hour, level
ORDER BY hour DESC;
```

## 🔧 Configuración Detallada

### LogConfig

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `name` | str | "app" | Nombre del logger |
| `level` | int/str | INFO | Nivel de logging |
| `environment` | str | "development" | Entorno (development/staging/production) |
| `log_dir` | Path | None | Directorio para archivos de log |
| `console_output` | bool | True | Output a consola |
| `file_output` | bool | True | Output a archivo |
| `rotate_logs` | bool | True | Rotación de archivos |
| `max_bytes` | int | 10MB | Tamaño máximo por archivo |
| `backup_count` | int | 5 | Número de backups |
| `json_format` | bool | False | Formato JSON |
| `mask_sensitive` | bool | True | Enmascarar datos sensibles |
| `postgres_enabled` | bool | False | Habilitar PostgreSQL |
| `postgres_config` | PostgreSQLConfig | None | Configuración de PostgreSQL |

### PostgreSQLConfig

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `host` | str | - | Host de PostgreSQL |
| `port` | int | 5432 | Puerto |
| `database` | str | "logs" | Nombre de base de datos |
| `user` | str | "postgres" | Usuario |
| `password` | str | "" | Contraseña |
| `table_name` | str | "application_logs" | Nombre de tabla |
| `schema` | str | "public" | Schema |
| `buffer_size` | int | 1000 | Tamaño del buffer |
| `batch_size` | int | 10 | Logs por lote |
| `flush_interval` | float | 5.0 | Intervalo de flush (segundos) |

## 🧪 Testing

```bash
# Instalar dependencias de desarrollo
poetry install --with dev

# Ejecutar tests
poetry run pytest

# Con coverage
poetry run pytest --cov=django_advanced_logging

# Ejecutar linters
poetry run black .
poetry run flake8
poetry run mypy django_advanced_logging
```

## 📚 Documentación

Documentación completa disponible en: [https://django-advanced-logging.readthedocs.io](https://django-advanced-logging.readthedocs.io)

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📝 Changelog

Ver [CHANGELOG.md](CHANGELOG.md) para ver los cambios entre versiones.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👤 Autor

**Tu Nombre**
- GitHub: [@tuusuario](https://github.com/tuusuario)
- Email: tu.email@example.com

## ⭐ Agradecimientos

Si este proyecto te resulta útil, ¡considera darle una estrella en GitHub! ⭐

## 🐛 Reportar Issues

Si encuentras un bug o tienes una sugerencia, por favor [abre un issue](https://github.com/tuusuario/django-advanced-logging/issues).

## 💡 Roadmap

- [ ] Soporte para más bases de datos (MySQL, MongoDB)
- [ ] Dashboard web para visualizar logs
- [ ] Integración con Sentry
- [ ] Métricas y alertas
- [ ] Soporte para logging distribuido
- [ ] CLI para gestión de logs

---