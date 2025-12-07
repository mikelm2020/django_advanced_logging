"""
Handlers personalizados para logging.

Este modulo contiene handlers especializados:
- PostgreSQLHandler: Guarda logs en PostgreSQL de forma asincrona
"""

import logging
import queue
import threading
import traceback
import json
import socket
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class PostgreSQLConfig:
    """
    Configuracion para la conexion a PostgreSQL.

    Attributes:
        host: Host del servidor PostgreSQL
        port: Puerto de PostgreSQL
        database: Nombre de la base de datos
        user: Usuario de PostgreSQL
        password: Contrasena
        table_name: Nombre de la tabla para logs
        schema: Schema de la base de datos
        ssl_mode: Modo SSL
        buffer_size: Tamano del buffer para escritura asincrona
        batch_size: Numero de logs a escribir por lote
        flush_interval: Intervalo en segundos para flush automatico

    Example:
        >>> config = PostgreSQLConfig(
        ...     host="localhost",
        ...     database="myapp",
        ...     user="postgres",
        ...     password="secret"
        ... )
    """
    host: str = "localhost"
    port: int = 5432
    database: str = "logs"
    user: str = "postgres"
    password: str = ""
    table_name: str = "application_logs"
    schema: str = "public"
    ssl_mode: str = "prefer"
    buffer_size: int = 1000
    batch_size: int = 10
    flush_interval: float = 5.0

    @property
    def connection_string(self) -> str:
        """
        Genera la cadena de conexion para PostgreSQL.

        Returns:
            String de conexion DSN
        """
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.database} "
            f"user={self.user} "
            f"password={self.password} "
            f"sslmode={self.ssl_mode}"
        )

    @classmethod
    def from_django_settings(cls, databases_config: dict = None) -> 'PostgreSQLConfig':
        """
        Crea configuracion desde Django DATABASES settings.

        Args:
            databases_config: Diccionario DATABASES de Django settings

        Returns:
            PostgreSQLConfig configurado
        """
        if databases_config is None:
            from django.conf import settings
            databases_config = getattr(settings, 'DATABASES', {})

        db_config = databases_config.get('default', {})

        return cls(
            host=db_config.get('HOST', 'localhost'),
            port=int(db_config.get('PORT', 5432)),
            database=db_config.get('NAME', 'postgres'),
            user=db_config.get('USER', 'postgres'),
            password=db_config.get('PASSWORD', ''),
        )


class PostgreSQLHandler(logging.Handler):
    """
    Handler que guarda logs en PostgreSQL de forma asincrona.

    Caracteristicas:
        - Escritura asincrona mediante cola (no bloquea la aplicacion)
        - Reconexion automatica en caso de perdida de conexion
        - Buffer para logs cuando la BD no esta disponible
        - Thread seguro
        - Soporte para campos personalizados (JSONB)

    Example:
        >>> config = PostgreSQLConfig(
        ...     host="localhost",
        ...     database="myapp",
        ...     user="postgres",
        ...     password="password"
        ... )
        >>> handler = PostgreSQLHandler(config)
        >>> handler.setLevel(logging.INFO)
        >>> logger.addHandler(handler)
    """

    def __init__(self, config: PostgreSQLConfig):
        """
        Inicializa el handler de PostgreSQL.

        Args:
            config: Configuracion de PostgreSQL
        """
        super().__init__()

        self.config = config
        self.log_queue: queue.Queue = queue.Queue(maxsize=config.buffer_size)
        self.connection = None
        self.connected = False
        self.writer_thread: Optional[threading.Thread] = None
        self.running = False
        self.logs_written = 0
        self.logs_failed = 0

        # Inicializar
        self._initialize()

    def _initialize(self) -> None:
        """Inicializa la conexion y el thread de escritura."""
        try:
            # Intentar importar psycopg (psycopg3) primero, luego psycopg2
            self.psycopg_module = None
            self.psycopg_version = None

            try:
                import psycopg
                self.psycopg_module = psycopg
                self.psycopg_version = 3
            except ImportError:
                try:
                    import psycopg2
                    self.psycopg_module = psycopg2
                    self.psycopg_version = 2
                except ImportError:
                    raise ImportError(
                        "Ni psycopg ni psycopg2 estan instalados. "
                        "Instala uno de estos:\n"
                        "  - pip install psycopg2-binary (recomendado)\n"
                        "  - pip install psycopg (psycopg3)"
                    )

            # Conectar
            self._connect()

            # Iniciar thread de escritura
            self._start_writer_thread()

        except Exception as e:
            print(f"Error al inicializar PostgreSQLHandler: {e}")
            print("IMPORTANTE: Asegurate de haber ejecutado "
                  "'python manage.py migrate' para crear la tabla de logs")
            traceback.print_exc()

    def _connect(self) -> None:
        """Establece conexion con PostgreSQL."""
        try:
            self.connection = self.psycopg_module.connect(
                self.config.connection_string
            )
            self.connection.autocommit = False
            self.connected = True
        except Exception as e:
            self.connected = False
            raise Exception(f"Error al conectar con PostgreSQL: {e}")

    def _start_writer_thread(self) -> None:
        """Inicia el thread de escritura asincrona."""
        self.running = True
        self.writer_thread = threading.Thread(
            target=self._writer_loop,
            daemon=True,
            name="PostgreSQLLogWriter"
        )
        self.writer_thread.start()

    def _writer_loop(self) -> None:
        """Loop principal del thread de escritura."""
        batch: List[logging.LogRecord] = []

        while self.running:
            try:
                try:
                    record = self.log_queue.get(timeout=self.config.flush_interval)
                    batch.append(record)
                except queue.Empty:
                    pass

                if len(batch) >= self.config.batch_size:
                    self._write_batch(batch)
                    batch = []
            except Exception as e:
                print(f"Error en writer_loop: {e}")

        # Escribir logs pendientes al cerrar
        if batch:
            self._write_batch(batch)

    def _write_batch(self, batch: List[logging.LogRecord]) -> None:
        """Escribe un lote de logs a PostgreSQL."""
        if not batch:
            return

        try:
            if not self.connected:
                self._connect()

            insert_sql = f"""
            INSERT INTO {self.config.schema}.{self.config.table_name} (
                timestamp, level, logger_name, message,
                module, function, line_number,
                thread_id, thread_name, process_id,
                exception, extra_data, environment, hostname
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            data = [self._prepare_record(record) for record in batch]

            with self.connection.cursor() as cursor:
                cursor.executemany(insert_sql, data)

            self.connection.commit()
            self.logs_written += len(batch)

        except Exception as e:
            if self.connection:
                try:
                    self.connection.rollback()
                except:
                    pass
            self.connected = False
            self.logs_failed += len(batch)
            print(f"Error al escribir batch de logs: {e}")

    def _prepare_record(self, record: logging.LogRecord) -> tuple:
        """Prepara un LogRecord para insercion en PostgreSQL."""
        timestamp = datetime.fromtimestamp(record.created)
        level = record.levelname
        logger_name = record.name
        message = self.format(record)
        module = record.module
        function = record.funcName
        line_number = record.lineno
        thread_id = record.thread
        thread_name = record.threadName
        process_id = record.process

        exception = None
        if record.exc_info:
            exception = (
                self.formatter.formatException(record.exc_info)
                if self.formatter
                else str(record.exc_info)
            )

        extra_data = {}
        if hasattr(record, 'extra_fields'):
            extra_data = record.extra_fields

        environment = getattr(record, 'environment', 'unknown')
        hostname = socket.gethostname()

        return (
            timestamp,
            level,
            logger_name,
            message,
            module,
            function,
            line_number,
            thread_id,
            thread_name,
            process_id,
            exception,
            json.dumps(extra_data) if extra_data else None,
            environment,
            hostname
        )

    def emit(self, record: logging.LogRecord) -> None:
        """Emite un log record a la cola para escritura asincrona."""
        try:
            self.log_queue.put_nowait(record)
        except queue.Full:
            # Si la cola esta llena, descartar el log mas antiguo
            try:
                self.log_queue.get_nowait()
                self.log_queue.put_nowait(record)
            except:
                pass

    def flush(self) -> None:
        """Fuerza la escritura de todos los logs pendientes."""
        try:
            self.log_queue.join()
        except:
            pass

    def close(self) -> None:
        """Cierra el handler y libera recursos."""
        self.running = False

        if self.writer_thread:
            self.writer_thread.join(timeout=10)

        if self.connection:
            try:
                self.connection.close()
            except:
                pass

        super().close()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadisticas del handler.

        Returns:
            Diccionario con estadisticas de logs escritos/fallidos
        """
        return {
            'logs_written': self.logs_written,
            'logs_failed': self.logs_failed,
            'queue_size': self.log_queue.qsize(),
            'connected': self.connected
        }
