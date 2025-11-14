# Guía de Docker para Django Advanced Logging

Esta guía explica cómo usar **django-advanced-logging** en ambientes Docker.

## 🎯 Filosofía

**django-advanced-logging** está diseñado para funcionar perfectamente en contenedores Docker sin configuración adicional:

1. ✅ **Una sola base de datos**: Los logs se guardan en la misma BD de tu proyecto Django
2. ✅ **Configuración por variables de entorno**: Todo se configura con ENV vars
3. ✅ **Zero-config**: Funciona out-of-the-box con configuración mínima
4. ✅ **Docker-first**: Optimizado para ambientes containerizados

## 🚀 Quick Start

### 1. Agregar al proyecto Django

```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_advanced_logging',
    ...
]
```

### 2. Variables de entorno

```env
# .env
POSTGRES_ENABLED=true
LOG_NAME=mi_proyecto
LOG_LEVEL=INFO
LOG_ENVIRONMENT=production
```

### 3. Ejecutar migración

```bash
docker-compose exec web python manage.py migrate
```

¡Listo! Los logs se están guardando en PostgreSQL.

## 📁 Estructura de Archivos

```
tu-proyecto/
├── docker-compose.yml
├── Dockerfile
├── .env
├── requirements.txt
├── manage.py
└── myproject/
    ├── settings.py
    ├── wsgi.py
    └── ...
```

## 🐳 Configuración Completa

### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: django_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
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
      # Base de datos (django-advanced-logging usa esta misma)
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/django_db
      
      # Logging
      POSTGRES_ENABLED: "true"
      LOG_NAME: mi_proyecto
      LOG_LEVEL: INFO
      LOG_ENVIRONMENT: production
      LOG_CONSOLE: "true"
      LOG_JSON: "true"
    depends_on:
      - postgres
    ports:
      - "8000:8000"

volumes:
  postgres_data:
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Crear directorio para logs de archivos (opcional)
RUN mkdir -p /app/logs

EXPOSE 8000

CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### requirements.txt

```txt
Django>=3.2
django-advanced-logging[postgresql]
psycopg2-binary
gunicorn
python-decouple
```

### .env

```env
# PostgreSQL
POSTGRES_PASSWORD=your_secure_password

# Django
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# django-advanced-logging
POSTGRES_ENABLED=true
LOG_NAME=mi_proyecto
LOG_LEVEL=INFO
LOG_ENVIRONMENT=production
LOG_CONSOLE=true
LOG_JSON=true
LOG_DB_TABLE=application_logs
```

## 💡 Mejores Prácticas

### 1. Configuración por Ambiente

```yaml
# docker-compose.prod.yml
services:
  web:
    environment:
      LOG_ENVIRONMENT: production
      LOG_LEVEL: WARNING
      LOG_JSON: "true"
      LOG_CONSOLE: "false"
      LOG_FILE: "true"

# docker-compose.dev.yml
services:
  web:
    environment:
      LOG_ENVIRONMENT: development
      LOG_LEVEL: DEBUG
      LOG_JSON: "false"
      LOG_CONSOLE: "true"
      LOG_FILE: "false"
```

### 2. Logs en Archivos + PostgreSQL

```yaml
services:
  web:
    volumes:
      - app_logs:/app/logs  # Logs en archivos
    environment:
      LOG_FILE: "true"
      LOG_DIR: /app/logs
      POSTGRES_ENABLED: "true"  # También en PostgreSQL
```

### 3. Health Checks

```yaml
services:
  web:
    healthcheck:
      test: ["CMD", "python", "-c", "import django; django.setup()"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 4. Multi-stage Build

```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
WORKDIR /app
COPY . .
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🔍 Debugging en Docker

### Ver logs en tiempo real

```bash
# Logs de Django
docker-compose logs -f web

# Logs de PostgreSQL
docker-compose logs -f postgres
```

### Consultar logs en la BD

```bash
# Conectar a PostgreSQL
docker-compose exec postgres psql -U postgres -d django_db

# Ver logs recientes
SELECT * FROM application_logs ORDER BY timestamp DESC LIMIT 10;

# Contar por nivel
SELECT level, COUNT(*) FROM application_logs GROUP BY level;
```

### Shell de Python

```bash
docker-compose exec web python manage.py shell

>>> from django_advanced_logging import get_logger
>>> logger = get_logger('test')
>>> logger.info("Test desde shell")
```

## 📊 Monitoreo

### Script de monitoreo

```bash
#!/bin/bash
# monitor_logs.sh

docker-compose exec postgres psql -U postgres -d django_db -c "
SELECT 
    level,
    COUNT(*) as count,
    MAX(timestamp) as last_seen
FROM application_logs 
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY level
ORDER BY count DESC;
"
```

### Alertas

```python
# myproject/monitoring.py
from django_advanced_logging import get_logger
import time

logger = get_logger('monitoring')

def check_error_rate():
    # Tu lógica para verificar errores
    error_rate = calculate_error_rate()
    
    if error_rate > 0.05:  # 5%
        logger.critical(
            f"Error rate alto: {error_rate*100}%",
            extra={
                'extra_fields': {
                    'error_rate': error_rate,
                    'threshold': 0.05,
                    'alert_type': 'high_error_rate'
                }
            }
        )
```

## 🔧 Troubleshooting

### Problema: Tabla no existe

```bash
# Solución: Ejecutar migraciones
docker-compose exec web python manage.py migrate
```

### Problema: No se conecta a PostgreSQL

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Ver logs de PostgreSQL
docker-compose logs postgres

# Probar conexión
docker-compose exec web python manage.py dbshell
```

### Problema: Logs no aparecen

```bash
# Verificar configuración
docker-compose exec web python -c "
from django.conf import settings
print('POSTGRES_ENABLED:', getattr(settings, 'LOGGING_CONFIG', {}).get('postgres_enabled'))
"

# Verificar variable de entorno
docker-compose exec web env | grep POSTGRES_ENABLED
```

## 🚀 Deploy en Producción

### 1. Usar secretos

```yaml
# docker-compose.prod.yml
services:
  web:
    environment:
      DATABASE_URL: ${DATABASE_URL}  # Desde variable de entorno del host
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY}
    env_file:
      - .env.production  # Archivo con secretos (no commiteado)
```

### 2. Limitar recursos

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### 3. Backups de logs

```bash
# Backup script
docker-compose exec postgres pg_dump -U postgres django_db -t application_logs > logs_backup.sql
```

## 📈 Escalabilidad

### Múltiples workers

```yaml
services:
  web:
    deploy:
      replicas: 3
    command: gunicorn myproject.wsgi:application --workers 4 --bind 0.0.0.0:8000
```

Todos los workers escriben a la misma tabla de logs sin conflictos gracias al buffer asíncrono.

## ✅ Checklist de Producción

- [ ] `POSTGRES_ENABLED=true`
- [ ] `LOG_JSON=true`
- [ ] `LOG_ENVIRONMENT=production`
- [ ] Migraciones ejecutadas
- [ ] Health checks configurados
- [ ] Backups de BD configurados
- [ ] Alertas configuradas
- [ ] Logs rotan correctamente
- [ ] Secretos en variables de entorno (no hardcodeados)

## 🔗 Recursos

- [INSTALL.md](INSTALL.md) - Guía de instalación completa
- [README.md](README.md) - Documentación general
- [examples/](examples/) - Ejemplos completos de Docker Compose

