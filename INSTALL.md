# Guía de Instalación - Django Advanced Logging

Esta guía te ayudará a instalar y configurar **django-advanced-logging** en tu proyecto Django, especialmente cuando usas Docker.

## 📋 Requisitos Previos

- Python ≥ 3.8
- Django ≥ 3.2
- PostgreSQL (opcional, pero recomendado)
- Docker y Docker Compose (si usas contenedores)

## 🚀 Instalación

### Opción 1: Instalación con pip

```bash
# Instalación básica
pip install django-advanced-logging

# Con soporte para PostgreSQL
pip install django-advanced-logging[postgresql]

# O con poetry
poetry add django-advanced-logging
poetry add django-advanced-logging -E postgresql
```

### Opción 2: Instalación desde el repositorio

```bash
# Desde GitHub
pip install git+https://github.com/tuusuario/django-advanced-logging.git

# O con poetry
poetry add git+https://github.com/tuusuario/django-advanced-logging.git
```

## ⚙️ Configuración en Django

### Paso 1: Agregar a INSTALLED_APPS

Edita tu `settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # django-advanced-logging (antes de tus apps)
    'django_advanced_logging',
    
    # Tus aplicaciones
    'myapp',
]
```

### Paso 2: Configuración Básica

**Opción A: Configuración automática (recomendado para Docker)**

El paquete se configura automáticamente usando variables de entorno. No necesitas agregar nada más a `settings.py`.

**Opción B: Configuración manual en settings.py**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LOGGING_CONFIG = {
    'name': 'mi_proyecto',
    'level': 'INFO',
    'environment': 'production' if not DEBUG else 'development',
    'log_dir': BASE_DIR / 'logs',
    'console_output': True,
    'file_output': True,
    'json_format': not DEBUG,  # JSON en producción
    'mask_sensitive': True,     # Enmascarar passwords, tokens, etc.
    'postgres_enabled': True,   # Habilitar logging a PostgreSQL
}
```

### Paso 3: Agregar Middleware (Opcional pero Recomendado)

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Logging de todas las peticiones HTTP
    'django_advanced_logging.django.middleware.LoggingMiddleware',
    
    # Logging de integraciones externas (ERPs, webhooks, APIs, Magento, etc.)
    'django_advanced_logging.django.integrations_middleware.ExternalIntegrationLoggingMiddleware',
]
```

### Paso 4: Ejecutar Migraciones

```bash
# Esto crea la tabla 'application_logs' en tu base de datos de Django
python manage.py migrate
```

**IMPORTANTE**: La tabla de logs se crea en la **misma base de datos** que tu proyecto Django (configurada en `DATABASES['default']`). No necesitas una base de datos separada.

## 🐳 Configuración con Docker

### Paso 1: Crear archivo `.env`

Copia `.env.example` a `.env` y ajusta las variables:

```env
# Logging Configuration
LOG_NAME=mi_proyecto
LOG_LEVEL=INFO
LOG_ENVIRONMENT=production
LOG_CONSOLE=true
LOG_FILE=true
LOG_JSON=true

# PostgreSQL Logging (usa la misma BD de Django)
POSTGRES_ENABLED=true
LOG_DB_TABLE=application_logs
LOG_BUFFER_SIZE=1000
LOG_BATCH_SIZE=10

# Django Database (django-advanced-logging usa esta misma configuración)
DATABASE_URL=postgresql://postgres:password@postgres:5432/django_db
```

### Paso 2: Dockerfile

Asegúrate de tener `django-advanced-logging` en tu `requirements.txt`:

```txt
Django>=3.2
django-advanced-logging[postgresql]
psycopg2-binary>=2.9.0
gunicorn
```

### Paso 3: Docker Compose

Tu `docker-compose.yml` debe tener:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: django_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: >
      sh -c "
        python manage.py migrate &&
        gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
      "
    environment:
      DATABASE_URL: postgresql://postgres:your_password@postgres:5432/django_db
      POSTGRES_ENABLED: "true"
      LOG_NAME: mi_proyecto
      LOG_LEVEL: INFO
      LOG_ENVIRONMENT: production
    depends_on:
      - postgres
```

### Paso 4: Levantar los contenedores

```bash
# Construir y levantar
docker-compose up -d --build

# Ver logs
docker-compose logs -f web

# Ejecutar migraciones (si no se hizo automáticamente)
docker-compose exec web python manage.py migrate
```

## 📝 Uso en tu Código

### Uso Básico

```python
from django_advanced_logging import get_logger

logger = get_logger(__name__)

logger.info("Aplicación iniciada")
logger.warning("Advertencia")
logger.error("Error")
```

### Con Campos Personalizados

```python
logger.info(
    "Usuario realizó una acción",
    extra={
        'extra_fields': {
            'user_id': request.user.id,
            'action': 'purchase',
            'amount': 99.99,
            'ip_address': request.META.get('REMOTE_ADDR'),
        }
    }
)
```

### En Views de Django

```python
from django.views import View
from django_advanced_logging import get_logger

logger = get_logger(__name__)

class MyView(View):
    def get(self, request):
        logger.info(
            f"Usuario {request.user} accedió a la vista",
            extra={
                'extra_fields': {
                    'user_id': request.user.id,
                    'path': request.path,
                    'method': request.method,
                }
            }
        )
        # Tu lógica aquí
        return Response({"status": "ok"})
```

### Con Decorador

```python
from django_advanced_logging import log_execution

@log_execution(logger_name='myapp.services', level='INFO')
def procesar_pedido(pedido_id):
    """Esta función se loggea automáticamente"""
    # Tu lógica aquí
    return {"status": "processed"}
```

## 🔍 Consultar Logs en PostgreSQL

```sql
-- Ver logs recientes
SELECT * FROM application_logs 
ORDER BY timestamp DESC 
LIMIT 100;

-- Logs con errores
SELECT * FROM application_logs 
WHERE level IN ('ERROR', 'CRITICAL')
ORDER BY timestamp DESC;

-- Buscar en campos personalizados (JSONB)
SELECT * FROM application_logs 
WHERE extra_data->>'user_id' = '123';

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

## 🔧 Configuración Avanzada

### Personalizar Rutas de Integración

Si usas el `ExternalIntegrationLoggingMiddleware`, puedes personalizar qué rutas monitorea:

```python
# settings.py

INTEGRATION_MONITORED_PATHS = [
    '/api/erp/',
    '/api/magento/',
    '/webhook/',
    '/api/custom/',  # Tu ruta personalizada
]

INTEGRATION_TYPES = {
    '/api/erp/': 'erp',
    '/api/magento/': 'magento',
    '/api/custom/': 'mi_integracion',
}
```

### Solo Variables de Entorno Necesarias

Si usas la configuración automática, estas son las variables mínimas:

```env
# Mínimo requerido
POSTGRES_ENABLED=true
LOG_NAME=mi_proyecto

# Opcional (tienen defaults)
LOG_LEVEL=INFO
LOG_ENVIRONMENT=production
LOG_CONSOLE=true
LOG_JSON=true
```

## 🧪 Verificar la Instalación

```bash
# En tu proyecto Django
python manage.py shell

>>> from django_advanced_logging import get_logger
>>> logger = get_logger('test')
>>> logger.info("Test de logging")
>>> # Verifica que aparezca en consola y en la BD
```

```sql
-- En PostgreSQL
SELECT * FROM application_logs WHERE logger_name LIKE '%test%';
```

## 📊 Monitoreo con Docker

```bash
# Ver logs de la aplicación
docker-compose logs -f web

# Conectar a PostgreSQL y ver logs
docker-compose exec postgres psql -U postgres -d django_db -c "SELECT * FROM application_logs ORDER BY timestamp DESC LIMIT 10;"

# Ver estadísticas
docker-compose exec postgres psql -U postgres -d django_db -c "SELECT level, COUNT(*) FROM application_logs GROUP BY level;"
```

## ⚠️ Troubleshooting

### Error: "table application_logs does not exist"

```bash
# Ejecutar migraciones
python manage.py migrate
# o en Docker
docker-compose exec web python manage.py migrate
```

### Error: "psycopg2 not installed"

```bash
pip install psycopg2-binary
# o
pip install django-advanced-logging[postgresql]
```

### Los logs no aparecen en PostgreSQL

1. Verifica que `POSTGRES_ENABLED=true`
2. Verifica que ejecutaste `migrate`
3. Verifica la configuración de la base de datos en Django
4. Revisa los logs de la aplicación para errores

### Warning: "PostgreSQL logging habilitado pero la base de datos no es PostgreSQL"

Tu `DATABASES['default']` no está configurado para PostgreSQL. Cambia el ENGINE a `django.db.backends.postgresql`.

## 📚 Recursos Adicionales

- [README.md](README.md) - Documentación general
- [CLAUDE.md](CLAUDE.md) - Guía para desarrollo
- [examples/](examples/) - Ejemplos completos
- [tests/](tests/) - Tests y ejemplos de uso

## 💡 Tips

1. **Producción**: Usa `LOG_JSON=true` para mejor parseo de logs
2. **Desarrollo**: Usa `LOG_JSON=false` y `LOG_CONSOLE=true` para debugging
3. **Performance**: Ajusta `LOG_BUFFER_SIZE` y `LOG_BATCH_SIZE` según tu carga
4. **Seguridad**: Los datos sensibles se enmascaran automáticamente
5. **Monitoreo**: Consulta la tabla regularmente y configura alertas

## 🤝 Soporte

Si encuentras problemas:
1. Revisa esta guía
2. Consulta los ejemplos en `examples/`
3. Abre un issue en GitHub
