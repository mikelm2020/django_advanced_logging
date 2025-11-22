# Advanced Logging

App Django auto-contenida para logging profesional y escalable.

## Que es esto?

Una aplicacion Django completa que puedes **copiar y pegar** en cualquier proyecto Django para tener un sistema de logging avanzado con:

- Logging a PostgreSQL de forma asincrona
- Formateo con colores para desarrollo
- Formato JSON para produccion
- Filtrado automatico de datos sensibles
- Middleware para logging de requests HTTP
- Panel de admin para visualizar logs
- Soporte para campos personalizados (JSONB)

## Instalacion Rapida

```bash
# 1. Copia la carpeta advanced_logging a tu proyecto
cp -r advanced_logging/ /ruta/a/tu/proyecto/

# 2. Agrega a INSTALLED_APPS en settings.py
INSTALLED_APPS = [
    ...
    'advanced_logging',
]

# 3. Ejecuta migraciones
python manage.py migrate

# 4. Usa!
from advanced_logging import get_logger
logger = get_logger(__name__)
logger.info("Hola mundo!")
```

## Documentacion

Ver [advanced_logging/README.md](advanced_logging/README.md) para documentacion completa.

## Dependencias

- Django >= 3.2
- psycopg2-binary (opcional, para PostgreSQL handler)

## Licencia

MIT - Usa libremente en cualquier proyecto.
