# Advanced Logging - App Django Auto-contenida

Sistema de logging profesional y escalable para proyectos Django.

## Caracteristicas

- Logging a PostgreSQL de forma asincrona (no bloquea la aplicacion)
- Multiples handlers (consola, archivo, PostgreSQL)
- Formateo con colores para desarrollo
- Formato JSON para produccion
- Filtrado de datos sensibles automatico
- Soporte para campos personalizados (JSONB)
- Middleware para logging de requests HTTP
- Admin integrado para visualizar logs
- Decoradores para logging automatico de funciones

## Instalacion

1. **Copia la carpeta `advanced_logging/` a tu proyecto Django**

```bash
cp -r advanced_logging/ /ruta/a/tu/proyecto/
```

2. **Agrega la app a INSTALLED_APPS en settings.py**

```python
INSTALLED_APPS = [
    ...
    'advanced_logging',
]
```

3. **Ejecuta las migraciones**

```bash
python manage.py migrate
```

4. **Opcionalmente, agrega el middleware**

```python
MIDDLEWARE = [
    ...
    'advanced_logging.middleware.LoggingMiddleware',
    # O para integraciones externas:
    # 'advanced_logging.middleware.ExternalIntegrationLoggingMiddleware',
]
```

## Uso Basico

```python
from advanced_logging import get_logger

logger = get_logger(__name__)

# Logs basicos
logger.debug("Mensaje de debug")
logger.info("Mensaje informativo")
logger.warning("Advertencia")
logger.error("Error")
logger.critical("Error critico")

# Con campos personalizados (se guardan en JSONB)
logger.info("Usuario logueado", extra={
    'extra_fields': {
        'user_id': 123,
        'ip': '192.168.1.1',
        'action': 'login'
    }
})

# Logging de excepciones
try:
    resultado = operacion_riesgosa()
except Exception as e:
    logger.error(f"Error en operacion: {e}", exc_info=True)
```

## Configuracion

### Configuracion via settings.py

```python
ADVANCED_LOGGING = {
    'name': 'mi_proyecto',
    'level': 'DEBUG',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'environment': 'development',  # development, staging, production
    'console_output': True,
    'file_output': False,
    'json_format': False,  # True para formato JSON (produccion)
    'postgres_enabled': True,  # Guardar logs en PostgreSQL
}
```

### Configuracion via variables de entorno

```bash
# Configuracion basica
export LOG_NAME=mi_proyecto
export LOG_LEVEL=INFO
export LOG_ENVIRONMENT=production
export LOG_CONSOLE=true
export LOG_FILE=false
export LOG_JSON=true

# PostgreSQL (si postgres_enabled=true)
export POSTGRES_ENABLED=true
export LOG_DB_HOST=localhost
export LOG_DB_PORT=5432
export LOG_DB_NAME=mi_base_de_datos
export LOG_DB_USER=postgres
export LOG_DB_PASSWORD=mi_password
```

## Decorador para Funciones

```python
from advanced_logging import log_execution

@log_execution(level="INFO")
def mi_funcion(parametro):
    """Esta funcion sera logueada automaticamente."""
    return parametro * 2

@log_execution(logger_name="my_app.calculos", level="DEBUG")
def calculo_complejo(datos):
    """Log con nombre de logger personalizado."""
    return sum(datos)
```

## Middleware

### LoggingMiddleware

Registra automaticamente todas las peticiones HTTP:

```python
MIDDLEWARE = [
    ...
    'advanced_logging.middleware.LoggingMiddleware',
]
```

Registra:
- Metodo y path del request
- Usuario (si esta autenticado)
- IP del cliente
- User-Agent
- Codigo de respuesta
- Tiempo de ejecucion
- Excepciones (con traceback)

### ExternalIntegrationLoggingMiddleware

Para logging detallado de integraciones externas (ERPs, APIs, webhooks):

```python
MIDDLEWARE = [
    ...
    'advanced_logging.middleware.ExternalIntegrationLoggingMiddleware',
]

# Opcional: Configurar paths a monitorear
INTEGRATION_MONITORED_PATHS = [
    '/api/erp/',
    '/api/payment/',
    '/webhook/',
]
```

## Admin

Accede a `/admin/advanced_logging/applicationlog/` para:

- Ver todos los logs con filtros
- Buscar por mensaje, logger, modulo
- Filtrar por nivel, entorno, fecha
- Ver excepciones formateadas
- Ver datos extra en JSON

## Comando de Prueba

```bash
# Probar logging basico
python manage.py test_logging

# Probar con nivel especifico
python manage.py test_logging --level DEBUG

# Verificar PostgreSQL
python manage.py test_logging --postgres

# Generar mas logs
python manage.py test_logging --count 10
```

## PostgreSQL Handler

El PostgreSQLHandler escribe logs de forma asincrona:

- No bloquea la aplicacion
- Escribe en batches para mejor rendimiento
- Reconexion automatica si se pierde conexion
- Thread seguro (funciona con Gunicorn/uWSGI)

La tabla se crea automaticamente con la migracion y tiene indices optimizados.

## Estructura de la Tabla

```sql
advanced_logging_applicationlog:
- id: BigAutoField
- timestamp: DateTime (indexado)
- level: VARCHAR(10) (indexado)
- logger_name: VARCHAR(255) (indexado)
- message: TEXT
- module: VARCHAR(100)
- function: VARCHAR(100)
- line_number: INTEGER
- thread_id: BIGINT
- thread_name: VARCHAR(100)
- process_id: INTEGER
- exception: TEXT
- extra_data: JSONB (indexado con GIN)
- environment: VARCHAR(50) (indexado)
- hostname: VARCHAR(255)
- created_at: DateTime
```

## Dependencias

### Requeridas
- Django >= 3.2

### Opcionales (para PostgreSQL Handler)
- psycopg2-binary (recomendado)
- psycopg (psycopg3)

```bash
pip install psycopg2-binary
# o
pip install psycopg
```

## Ejemplos de Consultas

### Buscar errores recientes

```python
from advanced_logging.models import ApplicationLog
from datetime import timedelta
from django.utils import timezone

# Errores de las ultimas 24 horas
errores = ApplicationLog.objects.filter(
    level__in=['ERROR', 'CRITICAL'],
    timestamp__gte=timezone.now() - timedelta(hours=24)
)
```

### Buscar por campos extra

```python
# Buscar logs de un usuario especifico
logs_usuario = ApplicationLog.objects.filter(
    extra_data__user_id=123
)

# Buscar por accion
logs_login = ApplicationLog.objects.filter(
    extra_data__action='login'
)
```

### Estadisticas

```python
from django.db.models import Count

# Conteo por nivel
stats = ApplicationLog.objects.values('level').annotate(
    total=Count('id')
).order_by('-total')
```

## Licencia

Uso interno - Copia libremente a cualquier proyecto Django.
