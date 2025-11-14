"""
Settings package con configuración por ambiente.

Estructura:
    settings/
        __init__.py       # Este archivo
        base.py           # Configuración base común
        local.py          # Desarrollo local
        development.py    # Desarrollo (CI/CD)
        staging.py        # Staging
        production.py     # Producción

Uso:
    export DJANGO_SETTINGS_MODULE=myproject.settings.production
"""

import os

# Determinar qué settings usar basado en variable de entorno
environment = os.getenv('DJANGO_ENVIRONMENT', 'local')

if environment == 'production':
    from .production import *
elif environment == 'staging':
    from .staging import *
elif environment == 'development':
    from .development import *
else:
    from .local import *
