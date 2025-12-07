#!/bin/bash
# Script para ejecutar los tests de advanced_logging

# Activar entorno virtual
source .venv/bin/activate

# Agregar directorio raíz al PYTHONPATH y ejecutar pytest
PYTHONPATH=/home/miguel/portfolio/django-advanced-logging:$PYTHONPATH pytest "$@"
