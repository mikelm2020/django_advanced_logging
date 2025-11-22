"""
Modelos Django para Advanced Logging.

Este modulo contiene el modelo ApplicationLog que representa
los logs almacenados en la base de datos.
"""

from django.db import models


class ApplicationLog(models.Model):
    """
    Modelo para almacenar logs de la aplicacion en PostgreSQL.

    Este modelo es usado por el PostgreSQLHandler para almacenar
    logs de forma asincrona, y por el admin para visualizarlos.

    Attributes:
        timestamp: Momento en que se genero el log
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger_name: Nombre del logger que genero el log
        message: Mensaje del log
        module: Modulo Python donde se genero el log
        function: Funcion donde se genero el log
        line_number: Linea de codigo donde se genero el log
        thread_id: ID del thread que genero el log
        thread_name: Nombre del thread
        process_id: ID del proceso
        exception: Traceback si hubo una excepcion
        extra_data: Campos personalizados en formato JSON
        environment: Entorno de ejecucion (development, staging, production)
        hostname: Nombre del servidor donde se genero el log
        created_at: Momento de insercion en la base de datos
    """

    class Level(models.TextChoices):
        """Niveles de logging disponibles."""
        DEBUG = 'DEBUG', 'Debug'
        INFO = 'INFO', 'Info'
        WARNING = 'WARNING', 'Warning'
        ERROR = 'ERROR', 'Error'
        CRITICAL = 'CRITICAL', 'Critical'

    timestamp = models.DateTimeField(
        verbose_name='Timestamp',
        db_index=True,
        help_text='Momento en que se genero el log'
    )

    level = models.CharField(
        max_length=10,
        choices=Level.choices,
        db_index=True,
        verbose_name='Nivel',
        help_text='Nivel de severidad del log'
    )

    logger_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name='Logger',
        help_text='Nombre del logger que genero el log'
    )

    message = models.TextField(
        verbose_name='Mensaje',
        help_text='Mensaje del log'
    )

    module = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Modulo',
        help_text='Modulo Python donde se genero el log'
    )

    function = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Funcion',
        help_text='Funcion donde se genero el log'
    )

    line_number = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Linea',
        help_text='Linea de codigo donde se genero el log'
    )

    thread_id = models.BigIntegerField(
        blank=True,
        null=True,
        verbose_name='Thread ID'
    )

    thread_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Thread'
    )

    process_id = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Process ID'
    )

    exception = models.TextField(
        blank=True,
        null=True,
        verbose_name='Excepcion',
        help_text='Traceback si hubo una excepcion'
    )

    extra_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Datos Extra',
        help_text='Campos personalizados en formato JSON'
    )

    environment = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
        verbose_name='Entorno',
        help_text='Entorno de ejecucion'
    )

    hostname = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Servidor',
        help_text='Nombre del servidor'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado',
        help_text='Momento de insercion en la base de datos'
    )

    class Meta:
        verbose_name = 'Log de Aplicacion'
        verbose_name_plural = 'Logs de Aplicacion'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['level']),
            models.Index(fields=['logger_name']),
            models.Index(fields=['environment']),
        ]

    def __str__(self):
        return f"[{self.level}] {self.timestamp} - {self.message[:50]}"

    @property
    def is_error(self) -> bool:
        """Indica si el log es de error o superior."""
        return self.level in ['ERROR', 'CRITICAL']

    @property
    def has_exception(self) -> bool:
        """Indica si el log tiene excepcion."""
        return bool(self.exception)
