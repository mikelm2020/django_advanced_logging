# Guía Multi-Ambiente - Django Advanced Logging

Esta guía explica cómo usar `django-advanced-logging` en diferentes ambientes (local, development, staging, production) con Docker, Poetry, y configuraciones específicas por ambiente.

## Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura Multi-Ambiente](#arquitectura-multi-ambiente)
3. [Configuración por Ambiente](#configuración-por-ambiente)
4. [Instalación del Paquete](#instalación-del-paquete)
5. [Configuración de Settings](#configuración-de-settings)
6. [Dockerfiles por Ambiente](#dockerfiles-por-ambiente)
7. [Docker Compose Overrides](#docker-compose-overrides)
8. [Variables de Entorno](#variables-de-entorno)
9. [Migraciones de Base de Datos](#migraciones-de-base-de-datos)
10. [Ejemplos de Uso](#ejemplos-de-uso)
11. [Troubleshooting](#troubleshooting)

---

## Visión General

`django-advanced-logging` está diseñado para funcionar en cualquier ambiente Django con:

- ✅ Django 3.2, 4.0, 4.1, 4.2 (incluyendo versiones específicas como 4.0.2)
- ✅ Python 3.8, 3.9, 3.10, 3.11, 3.12
- ✅ PostgreSQL con **psycopg2** O **psycopg3**
- ✅ Docker + Poetry en todos los ambientes
- ✅ Configuraciones específicas por ambiente
- ✅ La tabla de logs se crea en la **MISMA base de datos** del proyecto Django

---

## Arquitectura Multi-Ambiente

### Estructura de Ambientes

```
Tu Proyecto Django/
├── .env                          # Variables de entorno (no commitear)
├── .env.local.example            # Ejemplo para local
├── .env.dev.example              # Ejemplo para development
├── .env.staging.example          # Ejemplo para staging
├── .env.production.example       # Ejemplo para production
│
├── docker-compose.yml            # Configuración base de Docker
├── docker-compose.override.local.yml
├── docker-compose.override.dev.yml
├── docker-compose.override.staging.yml
├── docker-compose.override.production.yml
│
├── Dockerfile.local              # Dockerfile para desarrollo local
├── Dockerfile.dev                # Dockerfile para CI/CD dev
├── Dockerfile.staging            # Dockerfile para staging
├── Dockerfile.production         # Dockerfile para producción
│
├── pyproject.toml                # Dependencias con Poetry
├── poetry.lock
│
└── myproject/
    └── settings/
        ├── __init__.py           # Detecta ambiente automáticamente
        ├── base.py               # Configuración común
        ├── local.py              # Configuración local
        ├── development.py        # Configuración development
        ├── staging.py            # Configuración staging
        └── production.py         # Configuración production
```

### Flujo de Configuración

```
1. Docker lee COMPOSE_FILE → docker-compose.yml + override específico
2. Dockerfile específico del ambiente se ejecuta
3. Django settings/__init__.py lee DJANGO_SETTINGS_MODULE
4. Settings específico del ambiente se carga
5. django-advanced-logging se auto-configura desde DATABASES['default']
6. Tabla application_logs se crea con migrate
```

---

## Configuración por Ambiente

### Ambiente LOCAL (Desarrollo en tu máquina)

**Características:**
- DEBUG=True
- Logs en consola con colores
- Hot-reload de código
- PostgreSQL local o en container
- Formato de logs legible (no JSON)

**Dockerfile:** `Dockerfile.local`
**Compose:** `docker-compose.override.local.yml`
**Settings:** `settings/local.py`
**Env:** `.env.local.example`

---

### Ambiente DEVELOPMENT (CI/CD, servidor compartido)

**Características:**
- DEBUG=False
- Logs en JSON
- Gunicorn con 2 workers
- Redis cache
- Email SMTP

**Dockerfile:** `Dockerfile.dev`
**Compose:** `docker-compose.override.dev.yml`
**Settings:** `settings/development.py`
**Env:** `.env.dev.example`

---

### Ambiente STAGING (Pre-producción)

**Características:**
- Réplica de producción
- 2 replicas del servicio
- SSL habilitado
- Redis cache
- Sentry/New Relic
- Health checks

**Dockerfile:** `Dockerfile.staging`
**Compose:** `docker-compose.override.staging.yml`
**Settings:** `settings/staging.py`
**Env:** `.env.staging.example`

---

### Ambiente PRODUCTION (Producción)

**Características:**
- 4 replicas
- Seguridad máxima
- SSL estricto
- Redis con alta disponibilidad
- Backups automáticos
- Monitoring completo
- Logs solo WARNING+

**Dockerfile:** `Dockerfile.production`
**Compose:** `docker-compose.override.production.yml`
**Settings:** `settings/production.py`
**Env:** `.env.production.example`

---

## Instalación del Paquete

### Opción 1: Con psycopg2-binary (Recomendado)

```bash
# En tu proyecto Django con Poetry
poetry add django-advanced-logging -E postgresql
```

### Opción 2: Con psycopg3

```bash
poetry add django-advanced-logging -E postgresql3
```

### Opción 3: Con psycopg2 (sin binary)

```bash
poetry add django-advanced-logging -E postgresql2
```

### Verificar Instalación

```bash
poetry show django-advanced-logging
```

---

## Configuración de Settings

### 1. Crear Estructura de Settings

Copia los archivos de ejemplo desde `examples/settings/` a tu proyecto:

```bash
# Desde la raíz de tu proyecto
mkdir -p myproject/settings
cp examples/settings/* myproject/settings/
```

### 2. Configurar INSTALLED_APPS

En `settings/base.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Django Advanced Logging - debe estar DESPUÉS de las apps de Django
    'django_advanced_logging',

    # Tus apps
    'myapp',
]
```

### 3. Configurar MIDDLEWARE

En `settings/base.py`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Django Advanced Logging Middleware
    'django_advanced_logging.django.middleware.RequestLoggingMiddleware',
]
```

### 4. Configurar Database (IMPORTANTE)

El paquete usa la **MISMA base de datos** que tu proyecto Django.

En `settings/base.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'myproject'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '600')),
    }
}
```

### 5. Configurar Logging

En cada ambiente (`local.py`, `development.py`, etc.):

```python
# settings/local.py
LOGGING_CONFIG = {
    'name': 'myproject_local',
    'level': 'DEBUG',
    'environment': 'development',
    'console_output': True,
    'file_output': False,
    'json_format': False,
    'postgres_enabled': True,  # Habilita logging a PostgreSQL
}

# settings/production.py
LOGGING_CONFIG = {
    'name': 'myproject_prod',
    'level': 'WARNING',
    'environment': 'production',
    'console_output': False,
    'file_output': True,
    'json_format': True,
    'postgres_enabled': True,
}
```

---

## Dockerfiles por Ambiente

### LOCAL: Dockerfile.local

Copia desde `examples/Dockerfile.local` a la raíz de tu proyecto.

**Uso:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.local.yml up
```

**Características:**
- Monta el código como volumen (hot-reload)
- Instala dependencias de desarrollo
- Usa runserver
- Expone puerto 8000

---

### DEVELOPMENT: Dockerfile.dev

Copia desde `examples/Dockerfile.dev`.

**Uso:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.dev.yml up
```

**Características:**
- Gunicorn con 2 workers
- Solo dependencias de producción
- Límite de memoria: 512M

---

### STAGING: Dockerfile.staging

Copia desde `examples/Dockerfile.staging`.

**Uso:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.staging.yml up
```

**Características:**
- Multi-stage build
- 2 replicas
- Health checks
- Gunicorn con 4 workers

---

### PRODUCTION: Dockerfile.production

Copia desde `examples/Dockerfile.production`.

**Uso:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.production.yml up
```

**Características:**
- Build optimizado
- 4 replicas
- Rolling updates
- Backups automáticos
- Límite de memoria: 2GB

---

## Docker Compose Overrides

### Uso de Overrides

Docker Compose puede combinar múltiples archivos:

```bash
# LOCAL
export COMPOSE_FILE=docker-compose.yml:docker-compose.override.local.yml
docker-compose up

# DEVELOPMENT
export COMPOSE_FILE=docker-compose.yml:docker-compose.override.dev.yml
docker-compose up

# STAGING
export COMPOSE_FILE=docker-compose.yml:docker-compose.override.staging.yml
docker-compose up

# PRODUCTION
export COMPOSE_FILE=docker-compose.yml:docker-compose.override.production.yml
docker-compose up
```

O usando el flag `-f`:

```bash
docker-compose -f docker-compose.yml -f docker-compose.override.local.yml up
```

---

## Variables de Entorno

### 1. Crear archivo .env

```bash
# Para desarrollo local
cp examples/.env.local.example .env

# O para otros ambientes
cp examples/.env.dev.example .env.dev
cp examples/.env.staging.example .env.staging
cp examples/.env.production.example .env.production
```

### 2. Variables Clave

**Para django-advanced-logging:**

```bash
# Configuración de logging
LOG_NAME=myproject_local
LOG_LEVEL=DEBUG
LOG_ENVIRONMENT=development
LOG_CONSOLE=true
LOG_FILE=false
LOG_JSON=false

# PostgreSQL logging (usa misma BD de Django)
POSTGRES_ENABLED=true
LOG_DB_TABLE=application_logs
LOG_BUFFER_SIZE=1000
LOG_BATCH_SIZE=10
LOG_FLUSH_INTERVAL=5.0
```

**Base de datos (compartida con Django):**

```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=myproject
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

### 3. Secrets en Producción

**NO uses .env en producción.** Usa secrets manager:

- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes Secrets
- Docker Secrets

---

## Migraciones de Base de Datos

### IMPORTANTE: La tabla se crea en la MISMA base de datos

El paquete crea la tabla `application_logs` en la base de datos de Django.

### 1. Ejecutar Migraciones

```bash
# Con Docker
docker-compose exec web python manage.py migrate

# O directamente
poetry run python manage.py migrate
```

### 2. Verificar Tabla Creada

```sql
-- Conectar a PostgreSQL
\c myproject

-- Ver tabla
\d application_logs

-- Ver datos
SELECT id, timestamp, level, logger_name, message
FROM application_logs
ORDER BY timestamp DESC
LIMIT 10;
```

### 3. Schema de la Tabla

```sql
CREATE TABLE application_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    level VARCHAR(20) NOT NULL,
    logger_name VARCHAR(200) NOT NULL,
    message TEXT,
    module VARCHAR(200),
    function VARCHAR(200),
    line_number INTEGER,
    thread_id BIGINT,
    thread_name VARCHAR(200),
    process_id INTEGER,
    exception TEXT,
    extra_data JSONB,
    environment VARCHAR(50),
    hostname VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_application_logs_timestamp ON application_logs(timestamp DESC);
CREATE INDEX idx_application_logs_level ON application_logs(level);
CREATE INDEX idx_application_logs_logger ON application_logs(logger_name);
CREATE INDEX idx_application_logs_environment ON application_logs(environment);
CREATE INDEX idx_application_logs_extra_data ON application_logs USING GIN(extra_data);
```

---

## Ejemplos de Uso

### Ejemplo 1: Proyecto Nuevo

```bash
# 1. Crear proyecto Django
django-admin startproject myproject
cd myproject

# 2. Instalar django-advanced-logging
poetry add django-advanced-logging -E postgresql

# 3. Copiar archivos de configuración
mkdir -p myproject/settings
cp /ruta/django-advanced-logging/examples/settings/* myproject/settings/
cp /ruta/django-advanced-logging/examples/Dockerfile.* .
cp /ruta/django-advanced-logging/examples/docker-compose.override.* .
cp /ruta/django-advanced-logging/examples/.env.local.example .env

# 4. Configurar settings (editar base.py, local.py, etc.)

# 5. Levantar con Docker
docker-compose -f docker-compose.yml -f docker-compose.override.local.yml up -d

# 6. Ejecutar migraciones
docker-compose exec web python manage.py migrate

# 7. Crear superuser
docker-compose exec web python manage.py createsuperuser

# 8. Ver logs
docker-compose logs -f web
```

### Ejemplo 2: Proyecto Existente con Django 4.0.2

```bash
# Tu proyecto ya existe con Django 4.0.2 y psycopg2

# 1. Instalar el paquete
poetry add django-advanced-logging -E postgresql

# 2. Agregar a INSTALLED_APPS en settings.py
INSTALLED_APPS = [
    # ... tus apps existentes
    'django_advanced_logging',
]

# 3. Agregar middleware
MIDDLEWARE = [
    # ... middlewares existentes
    'django_advanced_logging.django.middleware.RequestLoggingMiddleware',
]

# 4. Configurar logging
LOGGING_CONFIG = {
    'name': 'myapp',
    'level': 'INFO',
    'environment': 'production',
    'console_output': True,
    'postgres_enabled': True,
}

# 5. Ejecutar migraciones
python manage.py migrate

# 6. Usar logging
from django_advanced_logging import get_logger

logger = get_logger(__name__)
logger.info("App iniciada", extra={
    'extra_fields': {'version': '1.0.0'}
})
```

### Ejemplo 3: Proyecto con psycopg3

```bash
# Tu proyecto usa psycopg (versión 3)

# 1. Instalar con soporte psycopg3
poetry add django-advanced-logging -E postgresql3

# 2. Verificar que se instaló psycopg
poetry show psycopg

# 3. El paquete detecta automáticamente psycopg3
# No necesitas configuración adicional

# 4. Ejecutar migraciones
python manage.py migrate

# El handler se conectará usando psycopg3 automáticamente
```

### Ejemplo 4: Migrar de Desarrollo a Staging

```bash
# 1. En desarrollo local
git add .
git commit -m "feat: agregar django-advanced-logging"
git push origin develop

# 2. Crear branch de staging
git checkout -b staging
git merge develop

# 3. Configurar variables de entorno de staging
# (usar secrets manager o CI/CD)
export DJANGO_SETTINGS_MODULE=myproject.settings.staging
export DB_HOST=staging-db.example.com
export DB_PASSWORD=<secret>

# 4. Build de imagen de staging
docker build -f Dockerfile.staging -t myproject:staging .

# 5. Deploy a staging
docker-compose -f docker-compose.yml -f docker-compose.override.staging.yml up -d

# 6. Ejecutar migraciones
docker-compose exec web python manage.py migrate

# 7. Verificar logs
docker-compose exec db psql -U postgres -d myproject -c \
  "SELECT * FROM application_logs ORDER BY timestamp DESC LIMIT 5;"
```

### Ejemplo 5: Deploy a Producción

```bash
# 1. Preparar release
git checkout main
git merge staging
git tag v1.0.0
git push origin main --tags

# 2. Build de imagen de producción
docker build -f Dockerfile.production -t myproject:v1.0.0 .
docker tag myproject:v1.0.0 myregistry.com/myproject:v1.0.0
docker push myregistry.com/myproject:v1.0.0

# 3. Configurar secrets (AWS, Vault, etc.)
aws secretsmanager create-secret \
  --name myproject/prod/db-password \
  --secret-string "super-secret-password"

# 4. Deploy con docker-compose
export COMPOSE_FILE=docker-compose.yml:docker-compose.override.production.yml
docker-compose pull
docker-compose up -d

# 5. Ejecutar migraciones
docker-compose exec web python manage.py migrate

# 6. Health check
curl https://myproject.com/health/

# 7. Verificar logs en PostgreSQL
docker-compose exec db psql -U postgres -d myproject -c \
  "SELECT COUNT(*) FROM application_logs WHERE environment='production';"
```

---

## Troubleshooting

### Error: "psycopg2 no está instalado"

```bash
# Solución 1: Instalar con extra
poetry add django-advanced-logging -E postgresql

# Solución 2: Instalar manualmente
poetry add psycopg2-binary

# Solución 3: Si tienes psycopg3
poetry add django-advanced-logging -E postgresql3
```

### Error: "Tabla application_logs no existe"

```bash
# Ejecutar migraciones
python manage.py migrate

# Verificar que django_advanced_logging esté en INSTALLED_APPS
python manage.py showmigrations django_advanced_logging
```

### Error: "Connection refused" a PostgreSQL

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Verificar variables de entorno
docker-compose exec web env | grep DB_

# Verificar conexión
docker-compose exec web python manage.py dbshell
```

### Los logs no aparecen en la base de datos

```bash
# 1. Verificar configuración
python manage.py shell
>>> from django.conf import settings
>>> settings.LOGGING_CONFIG
{'postgres_enabled': True, ...}

# 2. Verificar que el handler esté activo
>>> import logging
>>> logger = logging.getLogger('django_advanced_logging')
>>> logger.handlers

# 3. Verificar estadísticas del handler
>>> from django_advanced_logging import get_logger
>>> logger = get_logger(__name__)
>>> # El handler tiene estadísticas en logger.handlers[0].get_statistics()
```

### Logs duplicados

```bash
# Solución: Asegurar que propagate=False
# En settings/base.py
LOGGING = {
    'loggers': {
        'myapp': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,  # IMPORTANTE
        },
    },
}
```

### Error: "LoggerManager already initialized"

Esto es normal con el patrón Singleton. No es un error.

### Diferencias entre psycopg2 y psycopg3

El paquete detecta automáticamente cuál usar. Ambos funcionan igual.

```python
# El código interno detecta la versión:
try:
    import psycopg  # psycopg3
    self.psycopg_version = 3
except ImportError:
    import psycopg2  # psycopg2
    self.psycopg_version = 2
```

---

## Resumen de Comandos

```bash
# Instalación
poetry add django-advanced-logging -E postgresql

# Desarrollo local
cp examples/.env.local.example .env
docker-compose -f docker-compose.yml -f docker-compose.override.local.yml up
docker-compose exec web python manage.py migrate

# Development
cp examples/.env.dev.example .env.dev
docker-compose -f docker-compose.yml -f docker-compose.override.dev.yml up

# Staging
cp examples/.env.staging.example .env.staging
docker-compose -f docker-compose.yml -f docker-compose.override.staging.yml up

# Production
docker-compose -f docker-compose.yml -f docker-compose.override.production.yml up

# Ver logs en PostgreSQL
docker-compose exec db psql -U postgres -d myproject -c \
  "SELECT * FROM application_logs ORDER BY timestamp DESC LIMIT 10;"

# Limpiar logs antiguos
docker-compose exec db psql -U postgres -d myproject -c \
  "DELETE FROM application_logs WHERE timestamp < NOW() - INTERVAL '30 days';"
```

---

## Más Información

- **INSTALL.md**: Guía de instalación básica
- **DOCKER_GUIDE.md**: Guía específica de Docker
- **CLAUDE.md**: Documentación técnica y arquitectura
- **README.md**: Visión general del proyecto

---

**Última actualización:** 2025-11-13
