# Django Advanced Logging

> Sistema profesional y escalable de logging para proyectos Django con soporte para PostgreSQL, handlers asíncronos, formateo avanzado y filtrado de datos sensibles.

---

## Descripción

**Django Advanced Logging** es un paquete de **uso interno** diseñado para proporcionar capacidades avanzadas de logging a proyectos Django empresariales. Almacena logs en PostgreSQL de forma asíncrona, filtra automáticamente datos sensibles, y se integra perfectamente con Django usando la misma base de datos del proyecto.

### Características Principales

- **Logging Asíncrono a PostgreSQL**: Handler con queue thread-safe que no bloquea tu aplicación
- **Auto-configuración**: Usa automáticamente la configuración de `DATABASES['default']` de Django
- **Datos Sensibles Filtrados**: Enmascara passwords, tokens, API keys automáticamente
- **Campos Personalizados JSONB**: Almacena metadata estructurada para búsquedas avanzadas
- **Formatters Múltiples**: Colored formatter para desarrollo, JSON para producción
- **Middleware Incluido**: Logging automático de requests/responses HTTP con tiempos
- **Multi-entorno**: Configuraciones específicas para local, staging, producción
- **Compatible con psycopg2 y psycopg3**: Detecta y usa automáticamente la versión disponible
- **Thread-Safe**: Diseñado para aplicaciones concurrentes con Gunicorn/uWSGI
- **Docker Ready**: Ejemplos y configuraciones para todos los ambientes containerizados

---

## Requisitos

- **Django**: 3.2 o superior (compatible hasta 4.x)
- **PostgreSQL**: 12 o superior
- **Python**: 3.8+ (recomendado 3.10 o 3.11)
- **Poetry**: Para manejo de dependencias
- **psycopg2** o **psycopg3**: El paquete detecta automáticamente cual usar

---

## Instalación Rápida

### Para Desarrollo Local

Si estás probando el paquete en tu máquina:

```toml
# pyproject.toml de tu proyecto Django
[tool.poetry.dependencies]
django-advanced-logging = {path = "../django-advanced-logging", develop = true}

# Agregar psycopg según tu versión
psycopg = "^3.0.0"  # O psycopg2-binary = "^2.9.0"
```

```bash
poetry install
```

### Para Equipo/Staging/Producción

Una vez el paquete esté en Git:

```toml
# pyproject.toml de tu proyecto Django
[tool.poetry.dependencies]
django-advanced-logging = {git = "https://github.com/tu-empresa/django-advanced-logging.git", tag = "v1.0.0"}
```

```bash
poetry update django-advanced-logging
```

**📖 Instalación detallada**: Ver [LOCAL_INSTALLATION.md](./LOCAL_INSTALLATION.md)

---

## Configuración Django

### 1. Agregar a INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... otras apps
    'django_advanced_logging',  # ← Agregar aquí
]
```

### 2. Configurar LOGGING_CONFIG

```python
# settings.py

LOGGING_CONFIG = {
    'version': 1,
    'name': 'mi_proyecto',
    'environment': 'development',  # o 'staging' o 'production'
    'log_level': 'INFO',

    # Consola
    'console': {
        'enabled': True,
        'colored': True,  # Colores ANSI (útil en desarrollo)
    },

    # PostgreSQL - Se configura automáticamente desde DATABASES['default']
    'postgres': {
        'enabled': True,
        'table_name': 'application_logs',
        'buffer_size': 1000,
        'batch_size': 100,
        'flush_interval': 5.0,
    },

    # Filtros
    'filters': {
        'sensitive_data': True,  # Filtra passwords, tokens, etc.
        'environment': True,     # Agrega info de ambiente
    },
}
```

**Importante**: No necesitas especificar la conexión a PostgreSQL. El paquete **automáticamente** lee la configuración de `DATABASES['default']` de Django.

### 3. Aplicar Migraciones

```bash
# Crear tabla application_logs
python manage.py migrate django_advanced_logging
```

### 4. Agregar Middleware (Opcional)

Para logging automático de todas las requests HTTP:

```python
# settings.py
MIDDLEWARE = [
    # ... otros middleware
    'django_advanced_logging.django.middleware.LoggingMiddleware',
]
```

Este middleware loguea automáticamente:
- Método, path, query params
- Usuario autenticado
- IP del cliente y User-Agent
- Status code y tiempo de procesamiento
- Excepciones con traceback completo

**📖 Guía completa**: Ver [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)

---

## Uso Básico

### En tus Views

```python
from django_advanced_logging import get_logger

logger = get_logger(__name__)

def my_view(request):
    logger.info("Usuario accedió a la vista", extra={
        'extra_fields': {
            'user_id': request.user.id,
            'path': request.path,
            'method': request.method
        }
    })

    try:
        # Tu lógica de negocio
        result = process_data()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error procesando datos: {e}", extra={
            'extra_fields': {
                'user_id': request.user.id,
                'error_type': type(e).__name__
            }
        })
        raise
```

### En tus Modelos

```python
from django.db import models
from django_advanced_logging import get_logger

logger = get_logger(__name__)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def process_payment(self):
        logger.info("Procesando pago", extra={
            'extra_fields': {
                'order_id': self.id,
                'user_id': self.user.id,
                'amount': float(self.total)
            }
        })

        try:
            # Lógica de pago
            payment_result = charge_card(self.total)

            logger.info("Pago exitoso", extra={
                'extra_fields': {
                    'order_id': self.id,
                    'transaction_id': payment_result.id
                }
            })
        except PaymentError as e:
            logger.error(f"Error en pago: {e}", extra={
                'extra_fields': {
                    'order_id': self.id,
                    'error_code': e.code
                }
            })
            raise
```

### Decorator para Logging Automático

```python
from django_advanced_logging import log_execution

@log_execution(log_args=True, log_result=True)
def calculate_shipping(order_id, destination):
    """Esta función será logueada automáticamente"""
    # Tu código
    return {'cost': 15.99, 'days': 3}

# Genera logs como:
# INFO - Executing calculate_shipping with args=(order_id=123, destination='NY')
# INFO - calculate_shipping returned {'cost': 15.99, 'days': 3} in 0.045s
```

---

## Consultar Logs en PostgreSQL

Los logs se almacenan en la tabla `application_logs` con esta estructura:

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | bigint | Primary key |
| timestamp | timestamptz | Fecha/hora del log |
| logger_name | varchar(255) | Nombre del logger (ej: `myapp.views`) |
| level | varchar(50) | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| message | text | Mensaje del log |
| pathname | varchar(500) | Ruta del archivo fuente |
| lineno | integer | Línea del código fuente |
| funcname | varchar(100) | Nombre de la función |
| extra_data | jsonb | Campos personalizados (JSONB) |
| environment | varchar(50) | Ambiente (development, staging, production) |
| server_name | varchar(100) | Nombre del servidor/host |

### Queries Útiles

```sql
-- Últimos 50 logs
SELECT id, timestamp, level, logger_name, message
FROM application_logs
ORDER BY timestamp DESC
LIMIT 50;

-- Logs por nivel (últimas 24 horas)
SELECT level, COUNT(*) as count
FROM application_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY level
ORDER BY count DESC;

-- Buscar en campos personalizados (JSONB)
SELECT timestamp, message, extra_data
FROM application_logs
WHERE extra_data->>'user_id' = '123'
ORDER BY timestamp DESC;

-- Errores recientes con detalles
SELECT timestamp, logger_name, message, extra_data
FROM application_logs
WHERE level IN ('ERROR', 'CRITICAL')
  AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;

-- Logs por función (top 10)
SELECT funcname, COUNT(*) as calls
FROM application_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY funcname
ORDER BY calls DESC
LIMIT 10;

-- Performance: requests más lentas (requiere middleware)
SELECT
    extra_data->>'path' as path,
    AVG((extra_data->>'duration')::float) as avg_duration,
    COUNT(*) as requests
FROM application_logs
WHERE extra_data->>'duration' IS NOT NULL
  AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY extra_data->>'path'
ORDER BY avg_duration DESC
LIMIT 10;
```

---

## Configuración por Ambiente

### Desarrollo Local

```python
# settings/local.py
LOGGING_CONFIG = {
    'version': 1,
    'name': 'mi_proyecto',
    'environment': 'development',
    'log_level': 'DEBUG',  # Todo se loguea
    'console': {
        'enabled': True,
        'colored': True,  # Colores para mejor legibilidad
    },
    'postgres': {
        'enabled': True,
    },
}
```

### Staging

```python
# settings/staging.py
LOGGING_CONFIG = {
    'version': 1,
    'name': 'mi_proyecto',
    'environment': 'staging',
    'log_level': 'INFO',
    'console': {
        'enabled': True,
        'colored': False,  # Sin colores en logs de Docker
    },
    'file': {
        'enabled': True,
        'path': '/var/log/django/app.log',
        'max_bytes': 10485760,  # 10 MB
        'backup_count': 5,
    },
    'postgres': {
        'enabled': True,
        'batch_size': 200,
    },
}
```

### Producción

```python
# settings/production.py
LOGGING_CONFIG = {
    'version': 1,
    'name': 'mi_proyecto',
    'environment': 'production',
    'log_level': 'WARNING',  # Solo WARNING, ERROR, CRITICAL
    'console': {
        'enabled': False,  # Sin consola en producción
    },
    'file': {
        'enabled': True,
        'path': '/var/log/django/app.log',
        'max_bytes': 52428800,  # 50 MB
        'backup_count': 10,
    },
    'postgres': {
        'enabled': True,
        'buffer_size': 5000,  # Buffer más grande
        'batch_size': 500,    # Batches más grandes
        'flush_interval': 10.0,
    },
    'filters': {
        'sensitive_data': True,  # CRÍTICO en producción
        'environment': True,
    },
}
```

---

## Uso con Docker

### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    volumes:
      - .:/app
      # Para desarrollo local con path dependency:
      - ../django-advanced-logging:/django-advanced-logging:ro
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.local
    depends_on:
      - db

  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de Poetry
COPY pyproject.toml poetry.lock ./

# Instalar Poetry
RUN pip install poetry

# Configurar Poetry
RUN poetry config virtualenvs.create false

# Instalar dependencias
RUN poetry install --no-interaction --no-ansi

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

Consulta el directorio `examples/` para Dockerfiles por ambiente (local, dev, staging, production).

---

## Filtrado de Datos Sensibles

El paquete **automáticamente** filtra datos sensibles cuando `filters.sensitive_data = True`:

**Datos filtrados por defecto**:
- Passwords (password, passwd, pwd)
- Tokens (token, access_token, refresh_token, bearer)
- API Keys (api_key, apikey, secret_key)
- Claves privadas (private_key, secret)
- Cookies de sesión
- Números de tarjeta de crédito (patrón básico)

**Ejemplo**:

```python
logger.info("Login attempt", extra={
    'extra_fields': {
        'username': 'john',
        'password': 'super_secret_123',  # ← Será filtrado
        'api_token': 'abc123xyz',        # ← Será filtrado
    }
})
```

**Resultado en PostgreSQL**:
```json
{
  "username": "john",
  "password": "***FILTERED***",
  "api_token": "***FILTERED***"
}
```

---

## Testing

### Ejecutar Tests

```bash
# Todos los tests
poetry run pytest

# Con coverage
poetry run pytest --cov=django_advanced_logging

# Tests específicos
poetry run pytest tests/test_logger.py

# Verbose
poetry run pytest -v
```

### Code Quality

```bash
# Format con Black
poetry run black .

# Sort imports
poetry run isort .

# Linter
poetry run flake8

# Type checking
poetry run mypy django_advanced_logging
```

---

## Documentación Completa

### Guías Paso a Paso

1. **[LOCAL_INSTALLATION.md](./LOCAL_INSTALLATION.md)**
   - Instalación local para desarrollo
   - Instalación desde Git para producción
   - Uso con Docker y Poetry
   - Troubleshooting

2. **[IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)**
   - Integración en proyectos Django existentes
   - Configuración detallada
   - Ejemplos de uso
   - Verificación y testing

3. **[DEPLOYMENT.md](./DEPLOYMENT.md)**
   - Flujo de trabajo completo: Local → Equipo → Staging → Producción
   - Versionado y Git tags
   - Deploy con Docker
   - Rollback y mantenimiento

4. **[CLAUDE.md](./CLAUDE.md)**
   - Arquitectura del paquete
   - Componentes internos
   - Comandos de desarrollo
   - Notas técnicas

### Ejemplos

El directorio `examples/` contiene:
- `basic_usage.py`: Uso básico del paquete
- `django_settings.py`: Ejemplos de configuración
- `Dockerfile.local`: Dockerfile para desarrollo local
- `Dockerfile.dev`: Dockerfile para CI/CD
- `Dockerfile.staging`: Dockerfile para staging
- `Dockerfile.production`: Dockerfile optimizado para producción
- `docker-compose.override.*.yml`: Overrides por ambiente
- `settings/`: Settings por ambiente (base, local, staging, production)

---

## Workflow de Desarrollo

### 1. Desarrollo Local

```bash
# En tu proyecto Django
cd /home/miguel/portfolio/mi-proyecto-django

# Usar path dependency en pyproject.toml
# django-advanced-logging = {path = "../django-advanced-logging", develop = true}

poetry install
python manage.py migrate
python manage.py runserver
```

### 2. Preparar Release

```bash
# En el paquete
cd /home/miguel/portfolio/django-advanced-logging

# Tests
poetry run pytest

# Actualizar versión en pyproject.toml
# version = "1.0.0"

# Commit y tag
git commit -m "Release v1.0.0"
git tag v1.0.0
git push origin main --tags
```

### 3. Equipo Instala desde Git

```toml
# En proyecto Django del equipo
[tool.poetry.dependencies]
django-advanced-logging = {git = "https://github.com/tu-empresa/django-advanced-logging.git", tag = "v1.0.0"}
```

### 4. Deploy a Staging/Producción

```bash
# En servidor
git pull origin main
docker-compose -f docker-compose.yml -f docker-compose.override.production.yml up -d --build
docker-compose exec web python manage.py migrate
```

Ver [DEPLOYMENT.md](./DEPLOYMENT.md) para detalles completos.

---

## Troubleshooting

### "table application_logs does not exist"

**Solución**: Aplica las migraciones
```bash
python manage.py migrate django_advanced_logging
```

### "ModuleNotFoundError: No module named 'psycopg'"

**Solución**: Instala psycopg o psycopg2
```bash
poetry add psycopg  # Para psycopg3
# O
poetry add psycopg2-binary  # Para psycopg2
```

### Logs no aparecen en PostgreSQL

**Diagnóstico**:
1. Verifica que `postgres.enabled = True`
2. Verifica que aplicaste las migraciones
3. Verifica el nivel de log (si es WARNING pero logueas INFO, no se guardará)
4. Revisa logs de consola para errores del handler

### Performance Issues

**Solución**: Aumenta buffer y batch size
```python
LOGGING_CONFIG = {
    'postgres': {
        'buffer_size': 5000,
        'batch_size': 500,
        'flush_interval': 10.0,
    }
}
```

O reduce el nivel de log:
```python
LOGGING_CONFIG = {
    'log_level': 'WARNING',  # Solo WARNING, ERROR, CRITICAL
}
```

---

## Características Técnicas

### PostgreSQLHandler

- **Asíncrono**: Usa `queue.Queue` con thread dedicado para escritura
- **Batching**: Escribe logs en lotes configurables (default: 100)
- **Buffer**: Queue con tamaño configurable (default: 1000)
- **Auto-flush**: Flush automático cada N segundos (default: 5s)
- **Auto-reconnect**: Reconexión automática en caso de pérdida de conexión
- **Thread-safe**: Seguro para uso con Gunicorn/uWSGI workers
- **Estadísticas**: Expone métricas de escritura via `get_statistics()`

### Formatters

- **ColoredFormatter**: Colores ANSI para desarrollo (verde=INFO, amarillo=WARNING, rojo=ERROR)
- **JSONFormatter**: Formato JSON estructurado para producción/agregadores

### Filters

- **EnvironmentFilter**: Agrega información de ambiente (environment, server_name) a cada log
- **SensitiveDataFilter**: Filtra datos sensibles usando regex patterns configurables

### Django Integration

- **Auto-inicialización**: Se inicializa automáticamente al cargar Django si `LOGGING_CONFIG` existe
- **Auto-configuración DB**: Lee automáticamente `DATABASES['default']` de Django
- **Middleware**: Logging automático de requests con contexto completo
- **Migraciones**: Incluye migración para crear tabla `application_logs`

---

## Compatibilidad

| Componente | Versiones Soportadas |
|------------|---------------------|
| Python | 3.8, 3.9, 3.10, 3.11 |
| Django | 3.2, 4.0, 4.1, 4.2 |
| PostgreSQL | 12, 13, 14, 15, 16 |
| psycopg | 2.9+ (psycopg2) o 3.0+ (psycopg3) |

---

## Licencia

**Propietario** - Uso interno exclusivo de [Tu Empresa]

Este paquete es propiedad de la empresa y no está disponible públicamente. No debe ser distribuido fuera de la organización sin autorización.

---

## Soporte

Para problemas, preguntas o sugerencias:

1. Revisa la documentación en este repositorio
2. Consulta con el equipo de desarrollo
3. Revisa los issues existentes en el repositorio Git interno
4. Contacta al mantenedor del paquete

---

## Changelog

Ver [CHANGELOG.md](./CHANGELOG.md) para historial completo de cambios.

---

**Versión actual**: 1.0.0
**Última actualización**: 2024-01-15
