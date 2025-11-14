# Dockerfile de ejemplo para aplicación Django con django-advanced-logging
# Multi-stage build para optimizar el tamaño de la imagen

# ============================================================================
# STAGE 1: Builder
# ============================================================================
FROM python:3.11-slim as builder

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /build

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --user --no-warn-script-location -r requirements.txt

# ============================================================================
# STAGE 2: Runtime
# ============================================================================
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    DJANGO_SETTINGS_MODULE=myproject.settings

# Instalar dependencias de runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd -m -u 1000 appuser

# Copiar dependencias desde builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Cambiar al usuario no-root
USER appuser

# Directorio de trabajo
WORKDIR /app

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Crear directorio para logs
RUN mkdir -p /app/logs

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Comando por defecto
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
