"""
Ejemplo básico de uso de django-advanced-logging.

Este ejemplo muestra cómo usar el paquete en una aplicación Python/Django básica.
"""

# ============================================================================
# Ejemplo 1: Uso básico sin Django
# ============================================================================

from django_advanced_logging import get_logger

# Obtener un logger (se inicializa automáticamente)
logger = get_logger(__name__)

# Logging básico
logger.debug("Mensaje de debug")
logger.info("Mensaje informativo")
logger.warning("Advertencia")
logger.error("Error")
logger.critical("Error crítico")

# Logging con campos personalizados (se guardan en PostgreSQL como JSONB)
logger.info(
    "Usuario realizó una acción",
    extra={
        'extra_fields': {
            'user_id': 123,
            'action': 'login',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0...'
        }
    }
)

# ============================================================================
# Ejemplo 2: Configuración manual
# ============================================================================

from django_advanced_logging import initialize_logging, LogConfig, LogLevel, Environment

# Configurar el logging manualmente
config = LogConfig(
    name="mi_app",
    level=LogLevel.DEBUG,
    environment=Environment.DEVELOPMENT,
    console_output=True,
    file_output=True,
    json_format=False,  # True para producción
    log_dir="/app/logs"
)

# Inicializar con la configuración
manager = initialize_logging(config)

# Obtener logger
logger = manager.get_logger("mi_modulo")
logger.info("Logging configurado manualmente")

# ============================================================================
# Ejemplo 3: Configuración desde variables de entorno
# ============================================================================

from django_advanced_logging import initialize_from_env

# Inicializar desde variables de entorno (.env o Docker)
# Lee: LOG_NAME, LOG_LEVEL, LOG_ENVIRONMENT, POSTGRES_ENABLED, etc.
manager = initialize_from_env()

logger = get_logger("env_config")
logger.info("Configurado desde variables de entorno")

# ============================================================================
# Ejemplo 4: Con PostgreSQL
# ============================================================================

from django_advanced_logging import LogConfig, PostgreSQLConfig, LoggerManager

# Configuración de PostgreSQL
postgres_config = PostgreSQLConfig(
    host="localhost",  # o el nombre del servicio en Docker
    port=5432,
    database="app_logs",
    user="postgres",
    password="password",
    table_name="application_logs",
    buffer_size=1000,
    batch_size=10,
    flush_interval=5.0
)

# Configuración completa
config = LogConfig(
    name="mi_app_postgres",
    level=LogLevel.INFO,
    environment=Environment.PRODUCTION,
    postgres_enabled=True,
    postgres_config=postgres_config
)

manager = LoggerManager(config)
logger = manager.get_logger()

# Los logs se guardan en PostgreSQL de forma asíncrona
logger.info(
    "Orden procesada",
    extra={
        'extra_fields': {
            'order_id': 'ORD-12345',
            'customer_id': 789,
            'total_amount': 199.99,
            'payment_method': 'credit_card'
        }
    }
)

# ============================================================================
# Ejemplo 5: Decorator para logging automático
# ============================================================================

from django_advanced_logging import log_execution

@log_execution(logger_name='my_app.services', level='INFO')
def procesar_pedido(pedido_id, items):
    """
    Esta función se loggea automáticamente.
    
    Se registra:
    - Inicio de ejecución
    - Parámetros (cantidad de args/kwargs)
    - Finalización exitosa o error
    """
    print(f"Procesando pedido {pedido_id} con {len(items)} items")
    return {"status": "success", "order_id": pedido_id}

# Al llamar la función, se loggea automáticamente
resultado = procesar_pedido("ORD-001", ["item1", "item2", "item3"])

# ============================================================================
# Ejemplo 6: Manejo de excepciones
# ============================================================================

logger = get_logger("exception_handler")

try:
    # Código que puede fallar
    resultado = 10 / 0
except Exception as e:
    # Logging de excepción con traceback completo
    logger.error(
        f"Error al procesar: {str(e)}",
        exc_info=True,  # Incluye el traceback
        extra={
            'extra_fields': {
                'operation': 'division',
                'error_type': type(e).__name__
            }
        }
    )

# ============================================================================
# Ejemplo 7: Context manager (próxima versión)
# ============================================================================

# from django_advanced_logging import logging_context
#
# with logging_context(operation='importar_datos', user_id=123):
#     logger.info("Importando datos...")
#     # Todos los logs dentro de este context tendrán los campos extra
#     process_import()

print("✅ Ejemplos de uso básico completados!")
