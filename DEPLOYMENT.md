# Guía de Deployment - Django Advanced Logging

Esta guía describe el flujo de trabajo completo para desplegar `django-advanced-logging` desde tu máquina local hasta producción, pasando por el equipo de desarrollo y staging.

## Flujo de Trabajo Completo

```
Local (tu máquina)
    ↓
Git Repository (con tag)
    ↓
Equipo de Desarrollo
    ↓
Staging
    ↓
Producción
```

---

## 1. Desarrollo y Pruebas Locales

### Fase 1: Desarrollo del Paquete

En tu máquina, trabaja en el paquete usando path dependency:

```bash
# Ubicación del paquete
cd /home/miguel/portfolio/django-advanced-logging

# Hacer cambios al paquete
# ... editar código ...

# Ejecutar tests
poetry run pytest

# Verificar code quality
poetry run black .
poetry run flake8
poetry run mypy django_advanced_logging
```

### Fase 2: Probar en un Proyecto Django Local

En tu proyecto Django de pruebas:

**pyproject.toml**:
```toml
[tool.poetry.dependencies]
django-advanced-logging = {path = "../django-advanced-logging", develop = true}
```

```bash
# Instalar
poetry install

# Probar sin Docker
poetry run python manage.py migrate
poetry run python manage.py runserver

# Acceder a la app y generar logs
curl http://localhost:8000/

# Verificar logs en PostgreSQL
poetry run python manage.py dbshell
# SELECT * FROM application_logs ORDER BY timestamp DESC LIMIT 10;
```

### Fase 3: Probar con Docker

```bash
# Asegurarse que docker-compose.yml monte el paquete
# volumes:
#   - ../django-advanced-logging:/django-advanced-logging:ro

# Build y run
docker-compose up --build

# Verificar logs
docker-compose logs web

# Verificar en PostgreSQL
docker-compose exec db psql -U postgres -d mydb
# SELECT * FROM application_logs ORDER BY timestamp DESC LIMIT 10;
```

### Fase 4: Validación Final Local

Antes de subir a Git, verifica:

```bash
# 1. Tests pasan
cd /home/miguel/portfolio/django-advanced-logging
poetry run pytest -v

# 2. Code quality
poetry run black . --check
poetry run flake8
poetry run mypy django_advanced_logging

# 3. Build del paquete funciona
poetry build

# 4. Limpiar archivos generados
rm -rf dist/
```

---

## 2. Preparar Versión para el Equipo

### Paso 1: Versionado Semántico

Usa [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0 → 2.0.0): Cambios incompatibles con versiones anteriores
- **MINOR** (1.0.0 → 1.1.0): Nueva funcionalidad compatible con versiones anteriores
- **PATCH** (1.0.0 → 1.0.1): Bug fixes compatibles con versiones anteriores

Actualiza la versión en `pyproject.toml`:

```toml
[tool.poetry]
name = "django-advanced-logging"
version = "1.0.0"  # ← Actualizar aquí
```

### Paso 2: Crear CHANGELOG

Crea o actualiza `CHANGELOG.md`:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-01-15

### Added
- Initial release
- PostgreSQL async logging handler
- Django middleware for HTTP request logging
- Colored formatters for development
- JSON formatters for production
- Sensitive data filtering
- Support for psycopg3 and psycopg2
- Support for Django 3.2 to 4.x

### Fixed
- N/A

### Changed
- N/A

### Removed
- N/A
```

### Paso 3: Commit y Tag

```bash
cd /home/miguel/portfolio/django-advanced-logging

# Add todos los cambios
git add .

# Commit
git commit -m "Release v1.0.0

- Initial stable release
- PostgreSQL async logging
- Django middleware integration
- Multi-environment support
- Docker compatibility"

# Crear tag
git tag -a v1.0.0 -m "Version 1.0.0 - Initial Release"

# Ver tags
git tag

# Push incluyendo tags
git push origin main
git push origin v1.0.0
```

### Paso 4: Verificar en GitHub/GitLab

Verifica que el tag aparezca en tu repositorio:
- GitHub: Ve a "Releases" → deberías ver v1.0.0
- GitLab: Ve a "Repository" → "Tags"

---

## 3. Instalación por el Equipo de Desarrollo

### Comunicación al Equipo

Notifica a tu equipo vía Slack/Email:

```
📦 Nueva versión de django-advanced-logging disponible: v1.0.0

🔗 Repositorio: https://github.com/tu-empresa/django-advanced-logging
📋 Changelog: https://github.com/tu-empresa/django-advanced-logging/blob/main/CHANGELOG.md
📖 Docs: https://github.com/tu-empresa/django-advanced-logging/blob/main/IMPLEMENTATION_GUIDE.md

Para instalar:
1. Actualizar pyproject.toml con:
   django-advanced-logging = {git = "https://github.com/tu-empresa/django-advanced-logging.git", tag = "v1.0.0"}

2. Ejecutar: poetry update django-advanced-logging

3. Seguir la guía de implementación: IMPLEMENTATION_GUIDE.md
```

### Instalación por Desarrollador

Cada desarrollador del equipo:

**1. Actualizar pyproject.toml**:
```toml
[tool.poetry.dependencies]
django-advanced-logging = {git = "https://github.com/tu-empresa/django-advanced-logging.git", tag = "v1.0.0"}
```

**2. Actualizar dependencias**:
```bash
# Sin Docker
poetry update django-advanced-logging
poetry install

# Con Docker
docker-compose run --rm web poetry update django-advanced-logging
docker-compose run --rm web poetry install
```

**3. Aplicar migraciones**:
```bash
# Sin Docker
poetry run python manage.py migrate django_advanced_logging

# Con Docker
docker-compose run --rm web python manage.py migrate django_advanced_logging
```

**4. Configurar según IMPLEMENTATION_GUIDE.md**

---

## 4. Deployment a Staging

### Preparación

**1. Configuración específica de staging**:

**settings/staging.py**:
```python
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['staging.miapp.com']

LOGGING_CONFIG = {
    'version': 1,
    'name': 'mi_proyecto',
    'environment': 'staging',
    'log_level': 'INFO',
    'console': {
        'enabled': True,
        'colored': False,
    },
    'file': {
        'enabled': True,
        'path': '/var/log/django/app.log',
        'max_bytes': 10485760,  # 10 MB
        'backup_count': 5,
    },
    'postgres': {
        'enabled': True,
        'buffer_size': 2000,
        'batch_size': 200,
        'flush_interval': 5.0,
    },
    'filters': {
        'sensitive_data': True,
        'environment': True,
    },
}
```

**2. Docker compose override**:

**docker-compose.override.staging.yml**:
```yaml
version: '3.8'

services:
  web:
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.staging
      - SECRET_KEY=${SECRET_KEY}
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Deploy

```bash
# 1. SSH al servidor de staging
ssh user@staging.miapp.com

# 2. Navegar al proyecto
cd /app/mi-proyecto-django

# 3. Pull latest code
git pull origin main

# 4. Actualizar dependencias
docker-compose run --rm web poetry update django-advanced-logging

# 5. Build images
docker-compose -f docker-compose.yml -f docker-compose.override.staging.yml build

# 6. Aplicar migraciones
docker-compose -f docker-compose.yml -f docker-compose.override.staging.yml run --rm web python manage.py migrate

# 7. Deploy
docker-compose -f docker-compose.yml -f docker-compose.override.staging.yml up -d

# 8. Verificar logs
docker-compose logs -f web
```

### Verificación en Staging

**1. Health check**:
```bash
curl https://staging.miapp.com/health/
```

**2. Verificar logs en PostgreSQL**:
```bash
docker-compose exec db psql -U postgres -d mydb_staging
```

```sql
-- Ver últimos logs
SELECT id, timestamp, level, logger_name, message
FROM application_logs
ORDER BY timestamp DESC
LIMIT 20;

-- Ver distribución por nivel
SELECT level, COUNT(*) as count
FROM application_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY level
ORDER BY count DESC;
```

**3. Verificar archivos de log**:
```bash
docker-compose exec web tail -f /var/log/django/app.log
```

**4. Pruebas funcionales**:
- Acceder a la aplicación y generar diferentes tipos de requests
- Verificar que los logs se estén generando correctamente
- Verificar que datos sensibles estén filtrados
- Verificar tiempos de respuesta (el logging no debe impactar performance)

---

## 5. Deployment a Producción

### Pre-deployment Checklist

Antes de desplegar a producción, verifica:

- [ ] La versión ha estado corriendo en staging por al menos 48 horas sin problemas
- [ ] Los tests en staging pasaron exitosamente
- [ ] El equipo ha aprobado el deploy
- [ ] Tienes un plan de rollback
- [ ] Las configuraciones de producción están listas
- [ ] Los backups de la base de datos están actualizados

### Configuración de Producción

**settings/production.py**:
```python
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['miapp.com', 'www.miapp.com']

# Logging optimizado para producción
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
        'buffer_size': 5000,   # Buffer más grande
        'batch_size': 500,     # Batches más grandes
        'flush_interval': 10.0,  # Flush menos frecuente
    },
    'filters': {
        'sensitive_data': True,  # CRÍTICO en producción
        'environment': True,
    },
    'formatters': {
        'console': 'json',
        'file': 'json',
        'postgres': 'json',
    },
}
```

**docker-compose.override.production.yml**:
```yaml
version: '3.8'

services:
  web:
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - SECRET_KEY=${SECRET_KEY}
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 8 --timeout 120
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Deploy a Producción

**Opción A: Deploy Manual**

```bash
# 1. SSH al servidor de producción
ssh user@miapp.com

# 2. Navegar al proyecto
cd /app/mi-proyecto-django

# 3. Backup de la base de datos
docker-compose exec db pg_dump -U postgres mydb_production > backup_$(date +%Y%m%d_%H%M%S).sql

# 4. Pull latest code
git pull origin main

# 5. Actualizar dependencias
docker-compose run --rm web poetry update django-advanced-logging

# 6. Build images
docker-compose -f docker-compose.yml -f docker-compose.override.production.yml build

# 7. Aplicar migraciones (con downtime mínimo)
docker-compose -f docker-compose.yml -f docker-compose.override.production.yml run --rm web python manage.py migrate --no-input

# 8. Deploy con zero-downtime (rolling update)
docker-compose -f docker-compose.yml -f docker-compose.override.production.yml up -d --scale web=8
# Esperar que los nuevos contenedores estén healthy
sleep 30
docker-compose -f docker-compose.yml -f docker-compose.override.production.yml up -d --scale web=4

# 9. Verificar
docker-compose ps
docker-compose logs -f --tail=100 web
```

**Opción B: Deploy con CI/CD**

Si usas GitHub Actions, GitLab CI, o Jenkins:

**.github/workflows/deploy-production.yml**:
```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'  # Trigger en tags tipo v1.0.0

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2

      - name: Deploy to production
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /app/mi-proyecto-django
            git pull origin main
            docker-compose -f docker-compose.yml -f docker-compose.override.production.yml run --rm web poetry update django-advanced-logging
            docker-compose -f docker-compose.yml -f docker-compose.override.production.yml up -d --build
            docker-compose -f docker-compose.yml -f docker-compose.override.production.yml exec web python manage.py migrate --no-input
```

### Post-deployment Verificación

**1. Health checks**:
```bash
# Endpoint health
curl https://miapp.com/health/

# Todos los contenedores running
docker-compose ps
```

**2. Logs monitoring** (primeros 15 minutos):
```bash
# Logs en tiempo real
docker-compose logs -f web

# Errores
docker-compose logs web | grep ERROR

# Warnings
docker-compose logs web | grep WARNING
```

**3. Database logs**:
```sql
-- Ver logs recientes
SELECT level, COUNT(*) as count
FROM application_logs
WHERE timestamp > NOW() - INTERVAL '15 minutes'
GROUP BY level;

-- Ver errores
SELECT timestamp, logger_name, message
FROM application_logs
WHERE level = 'ERROR'
  AND timestamp > NOW() - INTERVAL '15 minutes'
ORDER BY timestamp DESC;
```

**4. Performance**:
```bash
# Response times
curl -w "@curl-format.txt" -o /dev/null -s https://miapp.com/

# Database connections
docker-compose exec db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

**5. Alertas**:
- Configurar alertas en tu sistema de monitoreo (Datadog, New Relic, etc.)
- Configurar alertas de errores en Sentry si lo usas
- Monitorear uso de disco (logs pueden crecer rápido)

---

## 6. Rollback

Si algo sale mal en producción:

### Rollback Rápido

```bash
# 1. Revertir a la versión anterior del paquete
cd /app/mi-proyecto-django

# Ver versión actual
docker-compose exec web poetry show django-advanced-logging

# Editar pyproject.toml para usar tag anterior
# django-advanced-logging = {git = "...", tag = "v0.9.0"}

# Actualizar
docker-compose run --rm web poetry update django-advanced-logging

# Rebuild y redeploy
docker-compose -f docker-compose.yml -f docker-compose.override.production.yml up -d --build

# 2. Si hay cambios de schema (migraciones), revertir migraciones
docker-compose exec web python manage.py migrate django_advanced_logging 0001_create_logs_table
# O completamente
# docker-compose exec web python manage.py migrate django_advanced_logging zero
```

### Rollback Completo

Si necesitas remover completamente el paquete:

```bash
# 1. Deshabilitar logging en settings
# LOGGING_CONFIG = {'postgres': {'enabled': False}}

# 2. Reload app
docker-compose restart web

# 3. Opcional: eliminar tabla de logs (solo si es necesario)
# docker-compose exec db psql -U postgres mydb_production
# DROP TABLE application_logs;
```

---

## 7. Mantenimiento y Actualizaciones

### Actualizar a Nueva Versión

Cuando salga una nueva versión (ej: v1.1.0):

**1. Desarrollo local**:
```bash
cd /home/miguel/portfolio/mi-proyecto-django

# Actualizar pyproject.toml
# django-advanced-logging = {git = "...", tag = "v1.1.0"}

poetry update django-advanced-logging
poetry run python manage.py migrate
poetry run python manage.py runserver
# Probar
```

**2. Equipo**:
- Notificar al equipo
- Cada desarrollador actualiza localmente
- Probar

**3. Staging**:
```bash
# Actualizar y probar en staging
git pull origin main
docker-compose run --rm web poetry update django-advanced-logging
docker-compose -f docker-compose.yml -f docker-compose.override.staging.yml up -d --build
```

**4. Producción** (después de 48h en staging sin problemas):
```bash
# Deploy siguiendo el proceso normal de producción
```

### Limpieza de Logs Antiguos

Los logs pueden crecer mucho. Configura limpieza periódica:

**1. Script de limpieza**:

**cleanup_logs.py**:
```python
from django.core.management.base import BaseCommand
from django.db import connection
from datetime import timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Cleanup old logs from application_logs table'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30,
                          help='Delete logs older than N days')

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)

        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM application_logs WHERE timestamp < %s",
                [cutoff_date]
            )
            deleted = cursor.rowcount

        self.stdout.write(
            self.style.SUCCESS(f'Deleted {deleted} logs older than {days} days')
        )
```

**2. Cron job**:
```bash
# crontab -e
# Ejecutar cada día a las 2 AM
0 2 * * * cd /app/mi-proyecto-django && docker-compose exec web python manage.py cleanup_logs --days=30
```

**3. O usando particiones de PostgreSQL** (recomendado para alto volumen):

```sql
-- Convertir tabla a particionada por mes
-- Esto requiere recrear la tabla, hazlo en mantenimiento planificado
```

---

## 8. Monitoreo

### Métricas Importantes

**1. Volumen de logs**:
```sql
-- Logs por día
SELECT DATE(timestamp) as date, COUNT(*) as count
FROM application_logs
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY date;

-- Logs por hora (último día)
SELECT DATE_TRUNC('hour', timestamp) as hour, COUNT(*) as count
FROM application_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour;
```

**2. Distribución por nivel**:
```sql
SELECT level, COUNT(*) as count
FROM application_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY level
ORDER BY count DESC;
```

**3. Top errores**:
```sql
SELECT message, COUNT(*) as occurrences
FROM application_logs
WHERE level = 'ERROR'
  AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY message
ORDER BY occurrences DESC
LIMIT 10;
```

**4. Performance del handler**:
```python
from django_advanced_logging import get_logger

logger = get_logger(__name__)

# El handler expone estadísticas
stats = logger.handlers[0].get_statistics()
print(stats)
# {'total_logs': 1234, 'failed_writes': 0, 'queue_size': 45}
```

### Alertas Recomendadas

Configure alertas para:
- ERROR level logs > 10 por minuto
- Tamaño de tabla application_logs > 10 GB
- Queue size del handler > 1000
- Failed writes > 0

---

## Best Practices

1. **Versionado**: Siempre usa tags semánticos (v1.0.0, v1.1.0)
2. **Testing**: Prueba en local → staging → producción (nunca saltes staging)
3. **Gradual rollout**: En producción, usa rolling updates
4. **Monitoring**: Los primeros 30 minutos después del deploy son críticos
5. **Backups**: Siempre haz backup antes de deploy a producción
6. **Documentation**: Actualiza CHANGELOG.md con cada versión
7. **Communication**: Notifica al equipo de cada deploy
8. **Log level**: Usa WARNING en producción, INFO en staging, DEBUG en local
9. **Performance**: Monitorea el impacto del logging en performance
10. **Cleanup**: Configura limpieza automática de logs antiguos

---

## Resumen del Flujo

```
1. Desarrollo local con path dependency
   ↓
2. Tests y validación
   ↓
3. Commit + Tag (v1.0.0)
   ↓
4. Push a Git
   ↓
5. Equipo instala desde Git
   ↓
6. Deploy a staging
   ↓
7. Validación en staging (48h)
   ↓
8. Deploy a producción
   ↓
9. Monitoreo post-deploy
   ↓
10. Mantenimiento y actualizaciones
```

Cada paso es crítico para un deploy exitoso y sin problemas.
