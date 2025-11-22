"""
Management command para probar el sistema de logging.

Uso:
    python manage.py test_logging
    python manage.py test_logging --level DEBUG
    python manage.py test_logging --postgres
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Comando para probar el sistema de logging."""

    help = 'Prueba el sistema de logging generando logs de ejemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--level',
            type=str,
            default='INFO',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='Nivel minimo de logs a generar'
        )
        parser.add_argument(
            '--postgres',
            action='store_true',
            help='Verifica si PostgreSQL handler esta activo'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Numero de logs de cada nivel a generar'
        )

    def handle(self, *args, **options):
        from advanced_logging import get_logger, get_logger_manager

        logger = get_logger('test_logging')
        level = options['level']
        count = options['count']

        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== Prueba de Advanced Logging ===\n'
            )
        )

        # Verificar manager
        manager = get_logger_manager()
        if manager:
            self.stdout.write(
                f"Logger Manager: {manager.config.name}\n"
                f"Environment: {manager.config.environment}\n"
                f"Level: {manager.config.level}\n"
                f"Console: {manager.config.console_output}\n"
                f"File: {manager.config.file_output}\n"
                f"JSON Format: {manager.config.json_format}\n"
            )
        else:
            self.stdout.write(
                self.style.WARNING('Logger Manager no inicializado')
            )

        # Generar logs de prueba
        self.stdout.write(
            self.style.SUCCESS(f'\n--- Generando {count} logs de cada nivel ---\n')
        )

        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        level_index = levels.index(level)

        for lvl in levels[level_index:]:
            for i in range(count):
                log_method = getattr(logger, lvl.lower())
                log_method(
                    f"Log de prueba {lvl} #{i+1}",
                    extra={
                        'extra_fields': {
                            'test_id': i + 1,
                            'level': lvl,
                            'source': 'test_logging_command'
                        }
                    }
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nLogs generados exitosamente!')
        )

        # Verificar PostgreSQL si se solicita
        if options['postgres']:
            self.stdout.write(
                self.style.SUCCESS('\n--- Verificando PostgreSQL Handler ---\n')
            )

            from advanced_logging.core.handlers import PostgreSQLHandler

            if manager:
                root_logger = manager.get_logger()
                pg_handlers = [
                    h for h in root_logger.handlers
                    if isinstance(h, PostgreSQLHandler)
                ]

                if pg_handlers:
                    for handler in pg_handlers:
                        stats = handler.get_statistics()
                        self.stdout.write(
                            f"PostgreSQL Handler activo:\n"
                            f"  - Logs escritos: {stats['logs_written']}\n"
                            f"  - Logs fallidos: {stats['logs_failed']}\n"
                            f"  - Cola actual: {stats['queue_size']}\n"
                            f"  - Conectado: {stats['connected']}\n"
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            'No hay PostgreSQL Handler configurado.\n'
                            'Para habilitarlo, configura POSTGRES_ENABLED=true '
                            'o agrega postgres_enabled=True en ADVANCED_LOGGING'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING('Logger Manager no disponible')
                )

        # Test de excepcion
        self.stdout.write(
            self.style.SUCCESS('\n--- Probando log de excepcion ---\n')
        )

        try:
            raise ValueError("Excepcion de prueba para verificar logging")
        except ValueError as e:
            logger.error(
                f"Excepcion capturada: {e}",
                exc_info=True,
                extra={
                    'extra_fields': {
                        'exception_type': 'ValueError',
                        'source': 'test_logging_command'
                    }
                }
            )

        self.stdout.write(
            self.style.SUCCESS(
                '\n=== Prueba completada ===\n'
                'Revisa la consola, archivos de log y/o la base de datos '
                'para verificar los logs generados.\n'
            )
        )
