# Guía de Implementación - Django Advanced Logging

Esta guía te llevará paso a paso para implementar `django-advanced-logging` en un proyecto Django existente que usa Docker, Docker Compose y Poetry.

## Tabla de Contenidos

1. [Prerrequisitos](#prerrequisitos)
2. [Instalación](#instalación)
3. [Configuración Django](#configuración-django)
4. [Migraciones](#migraciones)
5. [Configuración Avanzada](#configuración-avanzada)
6. [Uso en el Código](#uso-en-el-código)
7. [Verificación](#verificación)
8. [Configuración por Ambiente](#configuración-por-ambiente)
9. [Troubleshooting](#troubleshooting)

---

## Prerrequisitos

Antes de comenzar, verifica que tu proyecto cumpla con:

- ✅ Django 3.2 o superior (compatible hasta Django 4.x)
- ✅ PostgreSQL como base de datos (no funciona con SQLite, MySQL, etc.)
- ✅ Python 3.8+ (recomendado 3.10 o 3.11)
- ✅ Poetry para manejo de dependencias
- ✅ Docker y Docker Compose (opcional pero recomendado)

### Verificar PostgreSQL

En tu `settings.py`, verifica que uses PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # ✅ Debe ser postgresql
        'NAME': 'mi_base_datos',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'db',  # o 'localhost' si no usas Docker
        'PORT': '5432',
    }
}
```

---

## Instalación

### Paso 1: Agregar Dependencia

Abre el archivo `pyproject.toml` de tu proyecto Django y agrega la dependencia:

#### Opción A: Instalación Local (para desarrollo/pruebas)

```toml
[tool.poetry.dependencies]
python = "^3.10"
Django = "^4.0.2"
django-advanced-logging = {path = "../django-advanced-logging", develop = true}

# Agrega psycopg según la versión que uses
psycopg = "^3.0.0"  # Si usas psycopg3
# O
# psycopg2-binary = "^2.9.0"  # Si usas psycopg2
```

#### Opción B: Instalación desde Git (para equipo/staging/producción)

```toml
[tool.poetry.dependencies]
django-advanced-logging = {git = "https://github.com/tu-empresa/django-advanced-logging.git", tag = "v1.0.0"}
```

### Paso 2: Instalar Dependencias

```bash
# Sin Docker
poetry install

# Con Docker
docker-compose run --rm web poetry install
```

---

## Configuración Django

### Paso 1: Agregar a INSTALLED_APPS

En tu archivo `settings.py` (o `settings/base.py` si usas settings por ambiente):

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Tus apps
    'myapp',

    # Django Advanced Logging
    'django_advanced_logging',  # ← Agregar aquí
]
```

### Paso 2: Configurar LOGGING_CONFIG

Agrega la configuración de logging en tu `settings.py`:

#### Configuración Básica (Mínima)

```python
# settings.py

LOGGING_CONFIG = {
    'version': 1,
    'name': 'mi_proyecto',  # Nombre de tu proyecto
    'environment': 'development',  # O 'staging' o 'production'
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Configuración de consola
    'console': {
        'enabled': True,
        'colored': True,  # Colores ANSI en la consola (útil en desarrollo)
    },

    # Configuración de PostgreSQL
    'postgres': {
        'enabled': True,
        # NO necesitas especificar conexión, se toma automáticamente de DATABASES['default']
    },
}
```

**Importante**: El paquete **automáticamente** lee la configuración de PostgreSQL de `DATABASES['default']`. No necesitas duplicar la configuración de la base de datos.

#### Configuración Completa (Recomendada)

```python
# settings.py

LOGGING_CONFIG = {
    'version': 1,
    'name': 'mi_proyecto',
    'environment': 'development',  # Cambiar según ambiente
    'log_level': 'INFO',

    # Consola
    'console': {
        'enabled': True,
        'colored': True,
        'format': '[%(levelname)s] %(name)s - %(message)s',
    },

    # Archivo (opcional)
    'file': {
        'enabled': True,
        'path': '/var/log/django/app.log',
        'max_bytes': 10485760,  # 10 MB
        'backup_count': 5,
        'format': '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    },

    # PostgreSQL
    'postgres': {
        'enabled': True,
        'table_name': 'application_logs',  # Nombre de la tabla (default)
        'buffer_size': 1000,  # Buffer para logs antes de escribir
        'batch_size': 100,    # Escribe en lotes de 100
        'flush_interval': 5.0,  # Fuerza escritura cada 5 segundos
    },

    # Filtros
    'filters': {
        'sensitive_data': True,  # Filtra passwords, tokens, API keys
        'environment': True,     # Agrega info de ambiente a cada log
    },

    # Formatters
    'formatters': {
        'console': 'colored',  # 'colored' o 'json'
        'file': 'standard',    # 'standard' o 'json'
        'postgres': 'json',    # Siempre 'json' para postgres
    },
}
```

### Paso 3: Agregar Middleware (Opcional pero Recomendado)

Para logging automático de todas las requests HTTP:

```python
# settings.py

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Logging Middleware - Agregar al final
    'django_advanced_logging.django.middleware.LoggingMiddleware',  # ← Agregar aquí
]
```

Este middleware logueará automáticamente:
- Método HTTP (GET, POST, etc.)
- Path de la request
- Usuario autenticado (si existe)
- IP del cliente
- User-Agent
- Status code de la response
- Tiempo de procesamiento
- Excepciones (si ocurren)

---

## Migraciones

### Paso 1: Generar Migraciones

El paquete ya incluye las migraciones necesarias. Verifica que estén disponibles:

```bash
# Sin Docker
poetry run python manage.py showmigrations django_advanced_logging

# Con Docker
docker-compose exec web python manage.py showmigrations django_advanced_logging
```

Deberías ver:
```
django_advanced_logging
 [ ] 0001_create_logs_table
```

### Paso 2: Aplicar Migraciones

Aplica las migraciones para crear la tabla `application_logs` en tu base de datos:

```bash
# Sin Docker
poetry run python manage.py migrate django_advanced_logging

# Con Docker
docker-compose exec web python manage.py migrate django_advanced_logging
```

Salida esperada:
```
Running migrations:
  Applying django_advanced_logging.0001_create_logs_table... OK
```

### Paso 3: Verificar Tabla Creada

Conéctate a PostgreSQL y verifica:

```bash
# Sin Docker
psql -h localhost -U postgres -d mi_base_datos

# Con Docker
docker-compose exec db psql -U postgres -d mi_base_datos
```

En PostgreSQL:
```sql
\dt application_logs

-- Ver estructura
\d application_logs
```

Deberías ver la tabla con estas columnas:
- `id` (bigint, primary key)
- `timestamp` (timestamp with time zone)
- `logger_name` (varchar 255)
- `level` (varchar 50)
- `message` (text)
- `pathname` (varchar 500)
- `lineno` (integer)
- `funcname` (varchar 100)
- `extra_data` (jsonb)
- `environment` (varchar 50)
- `server_name` (varchar 100)

---

## Configuración Avanzada

### Logging de Integraciones Externas

Si tu proyecto hace llamadas a APIs externas, puedes usar el middleware especializado:

```python
# settings.py

MIDDLEWARE = [
    # ... otros middlewares
    'django_advanced_logging.django.middleware.LoggingMiddleware',
    'django_advanced_logging.django.integrations_middleware.ExternalIntegrationLoggingMiddleware',
]
```

Este middleware logueará automáticamente:
- Requests salientes (a APIs externas)
- Responses recibidas
- Tiempos de respuesta
- Errores de integración

### Filtrado de Datos Sensibles

El paquete automáticamente filtra datos sensibles si tienes `'sensitive_data': True` en los filtros.

Datos que se filtran por defecto:
- Passwords
- Tokens (Bearer, API tokens)
- API Keys
- Claves privadas
- Cookies de sesión
- Números de tarjeta de crédito (patrón básico)

Ejemplo de log antes del filtro:
```python
logger.info("User login", extra={
    'extra_fields': {
        'username': 'juan',
        'password': 'mi_password_secreto'  # ← Será filtrado
    }
})
```

Log después del filtro:
```json
{
  "username": "juan",
  "password": "***FILTERED***"
}
```

### Configuración por Ambiente

Es recomendable tener diferentes configuraciones según el ambiente:

#### `settings/base.py`

```python
# Configuración común a todos los ambientes
INSTALLED_APPS = [
    # ...
    'django_advanced_logging',
]
```

#### `settings/local.py`

```python
from .base import *

LOGGING_CONFIG = {
    'version': 1,
    'name': 'mi_proyecto',
    'environment': 'development',
    'log_level': 'DEBUG',  # DEBUG en local
    'console': {
        'enabled': True,
        'colored': True,  # Colores en local
    },
    'postgres': {
        'enabled': True,
    },
}
```

#### `settings/staging.py`

```python
from .base import *

LOGGING_CONFIG = {
    'version': 1,
    'name': 'mi_proyecto',
    'environment': 'staging',
    'log_level': 'INFO',
    'console': {
        'enabled': True,
        'colored': False,  # Sin colores en staging
    },
    'file': {
        'enabled': True,
        'path': '/var/log/django/app.log',
    },
    'postgres': {
        'enabled': True,
    },
}
```

#### `settings/production.py`

```python
from .base import *

LOGGING_CONFIG = {
    'version': 1,
    'name': 'mi_proyecto',
    'environment': 'production',
    'log_level': 'WARNING',  # Solo WARNING+ en producción
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
        'batch_size': 500,  # Lotes más grandes en producción
        'buffer_size': 5000,
    },
}
```

---

## Uso en el Código

### Importar Logger

```python
# En cualquier archivo de tu proyecto
from django_advanced_logging import get_logger

logger = get_logger(__name__)
```

### Logging Básico

```python
# views.py
from django_advanced_logging import get_logger

logger = get_logger(__name__)

def my_view(request):
    logger.info("Usuario accedió a my_view")

    try:
        # Tu código
        result = process_data()
        logger.info("Datos procesados exitosamente", extra={
            'extra_fields': {
                'result_count': len(result)
            }
        })
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error procesando datos: {e}", extra={
            'extra_fields': {
                'user_id': request.user.id if request.user.is_authenticated else None
            }
        })
        raise
```

### Logging con Campos Personalizados

```python
logger.info("Compra realizada", extra={
    'extra_fields': {
        'user_id': 123,
        'order_id': 'ORD-456',
        'amount': 99.99,
        'currency': 'USD',
        'payment_method': 'credit_card'
    }
})
```

Estos campos se almacenan en PostgreSQL como JSONB y puedes consultarlos así:

```sql
SELECT * FROM application_logs
WHERE extra_data->>'order_id' = 'ORD-456';

SELECT * FROM application_logs
WHERE (extra_data->>'amount')::numeric > 50.00;
```

### Decorator para Logging Automático

```python
from django_advanced_logging import log_execution

@log_execution(log_args=True, log_result=True)
def process_payment(order_id, amount):
    """Esta función será logueada automáticamente"""
    # Tu código
    return {'status': 'success', 'transaction_id': 'TXN-123'}
```

Esto generará logs como:
```
INFO - Executing process_payment with args=(order_id=456, amount=99.99)
INFO - process_payment returned {'status': 'success', 'transaction_id': 'TXN-123'} in 0.234s
```

### Logging de Excepciones

```python
try:
    risky_operation()
except Exception as e:
    logger.exception("Error en operación riesgosa", extra={
        'extra_fields': {
            'operation': 'risky_operation',
            'context': 'payment_processing'
        }
    })
```

---

## Verificación

### 1. Verificar en Consola

Ejecuta tu servidor Django:

```bash
# Sin Docker
poetry run python manage.py runserver

# Con Docker
docker-compose up
```

Deberías ver logs en la consola con colores (si `colored: True`):

```
[INFO] django.server - "GET / HTTP/1.1" 200 1234
[INFO] myapp.views - Usuario accedió a home page
```

### 2. Verificar en PostgreSQL

Consulta la tabla de logs:

```sql
-- Ver últimos 10 logs
SELECT id, timestamp, level, logger_name, message
FROM application_logs
ORDER BY timestamp DESC
LIMIT 10;

-- Ver logs por nivel
SELECT level, COUNT(*)
FROM application_logs
GROUP BY level;

-- Ver logs con campos personalizados
SELECT message, extra_data
FROM application_logs
WHERE extra_data IS NOT NULL
LIMIT 10;
```

### 3. Verificar Middleware

Haz una request HTTP a tu aplicación:

```bash
curl http://localhost:8000/
```

Consulta los logs:

```sql
SELECT * FROM application_logs
WHERE logger_name LIKE '%middleware%'
ORDER BY timestamp DESC
LIMIT 5;
```

Deberías ver logs con información de la request (método, path, status code, duración).

---

## Configuración por Ambiente

### Docker Compose con Overrides

Si usas docker-compose overrides por ambiente:

**docker-compose.yml** (base):
```yaml
version: '3.8'

services:
  web:
    build: .
    volumes:
      - .:/app
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/mydb

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

**docker-compose.override.local.yml**:
```yaml
version: '3.8'

services:
  web:
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.local
    command: python manage.py runserver 0.0.0.0:8000
```

**docker-compose.override.production.yml**:
```yaml
version: '3.8'

services:
  web:
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Ejecutar por ambiente:

```bash
# Local
docker-compose -f docker-compose.yml -f docker-compose.override.local.yml up

# Producción
docker-compose -f docker-compose.yml -f docker-compose.override.production.yml up
```

---

## Troubleshooting

### Error: "django_advanced_logging is not a registered app"

**Causa**: No agregaste el app a INSTALLED_APPS.

**Solución**:
```python
INSTALLED_APPS = [
    # ...
    'django_advanced_logging',
]
```

### Error: "table application_logs does not exist"

**Causa**: No aplicaste las migraciones.

**Solución**:
```bash
python manage.py migrate django_advanced_logging
```

### Error: "PostgreSQL logging enabled but database is not PostgreSQL"

**Causa**: Tu base de datos no es PostgreSQL.

**Solución**: Este paquete **requiere** PostgreSQL. Cambia tu `DATABASES['default']` para usar PostgreSQL:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # ...
    }
}
```

### Error: "ModuleNotFoundError: No module named 'psycopg'"

**Causa**: No tienes instalado psycopg o psycopg2.

**Solución**:
```bash
# Para psycopg3
poetry add psycopg

# Para psycopg2
poetry add psycopg2-binary
```

### Logs no aparecen en PostgreSQL

**Diagnóstico**:
1. Verifica que `postgres.enabled = True` en LOGGING_CONFIG
2. Verifica que aplicaste las migraciones
3. Verifica que tu nivel de log sea apropiado (ej: si tienes WARNING pero estás logueando INFO, no se guardará)
4. Revisa los logs de la consola para ver si hay errores del handler de PostgreSQL

**Solución**:
```python
# Aumenta temporalmente el nivel de log
LOGGING_CONFIG = {
    'log_level': 'DEBUG',  # ← Cambiar temporalmente
    # ...
}
```

### Datos sensibles no se filtran

**Causa**: No activaste el filtro de datos sensibles.

**Solución**:
```python
LOGGING_CONFIG = {
    # ...
    'filters': {
        'sensitive_data': True,  # ← Asegúrate que esté en True
    },
}
```

### Performance Issues con Muchos Logs

**Síntoma**: La aplicación se pone lenta con alto volumen de logs.

**Solución**: Aumenta el tamaño del buffer y batch:
```python
LOGGING_CONFIG = {
    'postgres': {
        'enabled': True,
        'buffer_size': 5000,   # ← Aumentar
        'batch_size': 500,     # ← Aumentar
        'flush_interval': 10.0,  # ← Aumentar
    },
}
```

O considera reducir el nivel de log en producción:
```python
LOGGING_CONFIG = {
    'log_level': 'WARNING',  # Solo WARNING, ERROR, CRITICAL
}
```

---

## Próximos Pasos

Una vez implementado y verificado:

1. ✅ Lee [DEPLOYMENT.md](./DEPLOYMENT.md) para estrategias de deploy
2. ✅ Revisa [README.md](./README.md) para ejemplos avanzados de uso
3. ✅ Consulta [LOCAL_INSTALLATION.md](./LOCAL_INSTALLATION.md) para detalles de instalación

## Soporte

Para problemas o preguntas:
- Revisa la documentación en el repositorio
- Consulta con el equipo de desarrollo
- Revisa los logs de Django para mensajes de error del paquete
