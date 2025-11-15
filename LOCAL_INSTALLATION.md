# Instalación Local - Django Advanced Logging

Este documento explica cómo instalar el paquete `django-advanced-logging` de forma local en tu máquina para pruebas y desarrollo, **sin necesidad de publicarlo en PyPI**.

## Contexto

Este paquete es para **uso interno** de la empresa y se instala directamente desde el repositorio local o Git, no desde PyPI. El flujo de trabajo típico es:

1. **Local**: Instalar y probar en tu máquina de desarrollo
2. **Equipo**: Una vez estable, el equipo lo instala desde el repositorio Git
3. **Staging**: Deploy a staging usando el repositorio Git
4. **Producción**: Deploy a producción usando el repositorio Git

## Prerrequisitos

- Python 3.8+ (recomendado 3.10 o 3.11)
- Poetry instalado (`pip install poetry`)
- Docker y Docker Compose (para ambientes containerizados)
- PostgreSQL (tu proyecto Django ya debe estar usando PostgreSQL)

## Estructura de Directorios Recomendada

Para pruebas locales, organiza tus proyectos así:

```
/home/miguel/portfolio/
├── django-advanced-logging/     # Este paquete
│   ├── django_advanced_logging/
│   ├── pyproject.toml
│   └── README.md
└── mi-proyecto-django/          # Tu proyecto Django existente
    ├── manage.py
    ├── pyproject.toml
    ├── docker-compose.yml
    └── Dockerfile
```

## Método 1: Instalación Local con Path Dependency (Desarrollo)

### Paso 1: Ubicar el Paquete

Asegúrate de que el paquete `django-advanced-logging` esté en una ubicación accesible en tu máquina:

```bash
cd /home/miguel/portfolio/django-advanced-logging
pwd  # Anota esta ruta
```

### Paso 2: Agregar Dependencia en tu Proyecto Django

En el `pyproject.toml` de tu proyecto Django, agrega el paquete usando una path dependency:

```toml
[tool.poetry.dependencies]
python = "^3.10"
Django = "^4.0.2"  # O la versión que uses
django-advanced-logging = {path = "../django-advanced-logging", develop = true}

# Si usas psycopg3
psycopg = "^3.0.0"

# O si usas psycopg2
# psycopg2-binary = "^2.9.0"
```

**Nota**: El parámetro `develop = true` permite que los cambios en el paquete se reflejen inmediatamente sin necesidad de reinstalar.

### Paso 3: Instalar Dependencias

```bash
cd /home/miguel/portfolio/mi-proyecto-django
poetry install
```

Esto instalará el paquete desde la ruta local especificada.

### Paso 4: Verificar Instalación

```bash
poetry show django-advanced-logging
```

Deberías ver la información del paquete con la ruta local.

## Método 2: Instalación desde Git (Equipo/Staging/Producción)

Una vez que el paquete esté estable y subido a Git, todo el equipo puede instalarlo así:

```toml
[tool.poetry.dependencies]
django-advanced-logging = {git = "https://github.com/tu-empresa/django-advanced-logging.git"}

# O especificando una rama
django-advanced-logging = {git = "https://github.com/tu-empresa/django-advanced-logging.git", branch = "main"}

# O especificando un tag/version
django-advanced-logging = {git = "https://github.com/tu-empresa/django-advanced-logging.git", tag = "v1.0.0"}
```

## Instalación en Docker

### Opción A: Path Dependency en Docker (Desarrollo Local)

Cuando uses Docker localmente con path dependency, necesitas montar ambos directorios:

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  web:
    build: .
    volumes:
      # Monta tu proyecto
      - .:/app
      # Monta el paquete django-advanced-logging
      - ../django-advanced-logging:/django-advanced-logging:ro
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.local
    depends_on:
      - db

  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: myproject_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY pyproject.toml poetry.lock ./

# Instalar poetry
RUN pip install poetry

# Configurar poetry para no crear virtualenv
RUN poetry config virtualenvs.create false

# Instalar dependencias
# Nota: El path dependency será resuelto por el volumen montado
RUN poetry install --no-interaction --no-ansi

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### Opción B: Git Dependency en Docker (Staging/Producción)

Para staging y producción, usa la dependencia Git en lugar de path:

**pyproject.toml**:
```toml
[tool.poetry.dependencies]
django-advanced-logging = {git = "https://github.com/tu-empresa/django-advanced-logging.git", tag = "v1.0.0"}
```

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar git y dependencias
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY pyproject.toml poetry.lock ./

# Instalar poetry
RUN pip install poetry

# Configurar poetry
RUN poetry config virtualenvs.create false

# Instalar dependencias (poetry descargará desde Git)
RUN poetry install --no-interaction --no-ansi --no-dev

COPY . .

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Verificación de Instalación

Después de instalar, verifica que el paquete funcione correctamente:

### 1. Verificar en el Shell de Django

```bash
poetry run python manage.py shell
```

```python
from django_advanced_logging import get_logger

logger = get_logger(__name__)
logger.info("Test desde shell", extra={
    'extra_fields': {
        'test': True,
        'ambiente': 'local'
    }
})
```

### 2. Verificar en Docker

```bash
docker-compose up -d
docker-compose exec web python manage.py shell
```

Ejecuta el mismo código de prueba.

### 3. Verificar Migraciones

```bash
poetry run python manage.py showmigrations django_advanced_logging
```

Deberías ver:
```
django_advanced_logging
 [ ] 0001_create_logs_table
```

Aplica las migraciones:
```bash
poetry run python manage.py migrate django_advanced_logging
```

## Troubleshooting

### Error: "No module named 'django_advanced_logging'"

**Solución**: Verifica que la ruta en `pyproject.toml` sea correcta:
```bash
cd /home/miguel/portfolio/mi-proyecto-django
ls ../django-advanced-logging  # Debe mostrar el contenido del paquete
```

### Error: "ModuleNotFoundError: No module named 'psycopg'"

**Solución**: Instala la versión correcta de psycopg según tu proyecto:
```bash
# Para psycopg3
poetry add psycopg

# Para psycopg2
poetry add psycopg2-binary
```

### Error en Docker: "Could not find a version that matches..."

**Solución**: Asegúrate de que el volumen esté montado correctamente en docker-compose.yml:
```yaml
volumes:
  - ../django-advanced-logging:/django-advanced-logging:ro
```

### Path Dependency no Actualiza Cambios

**Solución**: Usa `develop = true` en pyproject.toml:
```toml
django-advanced-logging = {path = "../django-advanced-logging", develop = true}
```

Luego reinstala:
```bash
poetry install
```

## Workflow Recomendado

### 1. Desarrollo Local (Tu Máquina)

```bash
# 1. Clonar el paquete
git clone git@github.com:tu-empresa/django-advanced-logging.git

# 2. En tu proyecto Django, agregar path dependency
# pyproject.toml:
# django-advanced-logging = {path = "../django-advanced-logging", develop = true}

# 3. Instalar
poetry install

# 4. Probar sin Docker
poetry run python manage.py migrate
poetry run python manage.py runserver

# 5. Probar con Docker
docker-compose up --build
```

### 2. Compartir con el Equipo

```bash
# 1. Hacer commit y push del paquete
cd /home/miguel/portfolio/django-advanced-logging
git add .
git commit -m "Versión estable v1.0.0"
git tag v1.0.0
git push origin main --tags

# 2. Actualizar pyproject.toml del proyecto para usar Git
# django-advanced-logging = {git = "...", tag = "v1.0.0"}

# 3. El equipo actualiza dependencias
poetry update django-advanced-logging
```

### 3. Deploy a Staging/Producción

```bash
# 1. Usar Git dependency con tag específico
# django-advanced-logging = {git = "...", tag = "v1.0.0"}

# 2. Build y deploy
docker-compose -f docker-compose.yml -f docker-compose.override.staging.yml build
docker-compose -f docker-compose.yml -f docker-compose.override.staging.yml up -d

# 3. Aplicar migraciones
docker-compose exec web python manage.py migrate
```

## Próximos Pasos

Consulta los siguientes documentos para implementar el paquete en tu proyecto:

- **[IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)**: Guía paso a paso para implementar en proyectos Django existentes
- **[DEPLOYMENT.md](./DEPLOYMENT.md)**: Estrategias de deploy para diferentes ambientes
- **[README.md](./README.md)**: Documentación general del paquete y ejemplos de uso
