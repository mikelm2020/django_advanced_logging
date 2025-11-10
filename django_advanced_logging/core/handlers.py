"""
Handlers personalizados para logging.

Este módulo contiene handlers especializados como PostgreSQLHandler
que permite guardar logs en PostgreSQL de forma asíncrona.
"""

import logging
import logging.handlers
import queue
import threading
import traceback
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class PostgreSQLConfig:
    """
    Configuración para la conexión a PostgreSQL.
    
    Attributes:
        host: Host del servidor PostgreSQL
        port: Puerto de PostgreSQL
        database: Nombre de la base de datos
        user: Usuario de PostgreSQL
        password: Contraseña
        table_name: Nombre de la tabla para logs
        schema: Schema de la base de datos (default: public)
        ssl_mode: Modo SSL (disable, allow, prefer, require, verify-ca, verify-full)
        buffer_size: Tamaño del buffer para escritura asíncrona
        batch_size: Número de logs a escribir por lote
        flush_interval: Intervalo en segundos para flush automático
    
    Example:
        >>> pg_config = PostgreSQLConfig(
        ...     host="localhost",
        ...     port=5432,
        ...     database="app_logs",
        ...     user="logger",
        ...     password="secure_password",
        ...     table_name="application_logs"
        ... )
    """
    host: str
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
        Genera la cadena de conexión para PostgreSQL.
        
        Returns:
            String de conexión DSN
        """
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.database} "
            f"user={self.user} "
            f"password={self.password} "
            f"sslmode={self.ssl_mode}"
        )


class PostgreSQLHandler(logging.Handler):
    """
    Handler que guarda logs en PostgreSQL de forma asíncrona.
    
    Características:
        - Escritura asíncrona mediante cola (no bloquea la aplicación)
        - Reconexión automática en caso de pérdida de conexión
        - Creación automática de tabla si no existe
        - Buffer para logs cuando la BD no está disponible
        - Thread seguro
        - Soporte para campos personalizados (JSONB)
    
    Example:
        >>> pg_config = PostgreSQLConfig(
        ...     host="localhost",
        ...     database="app_logs",
        ...     user="logger",
        ...     password="password"
        ... )
        >>> pg_handler = PostgreSQLHandler(pg_config)
        >>> pg_handler.setLevel(logging.INFO)
    """
    
    def __init__(self, config: PostgreSQLConfig):
        """
        Inicializa el handler de PostgreSQL.
        
        Args:
            config: Configuración de PostgreSQL
        """
        super().__init__()
        
        self.config = config
        self.log_queue = queue.Queue(maxsize=config.buffer_size)
        self.connection = None
        self.connected = False
        self.writer_thread = None
        self.running = False
        self.logs_written = 0
        self.logs_failed = 0
        
        # Inicializar
        self._initialize()
    
    def _initialize(self) -> None:
        """Inicializa la conexión (sin crear tabla)."""
        try:
            # Importar psycopg2
            try:
                import psycopg2
                self.psycopg2 = psycopg2
            except ImportError:
                raise ImportError(
                    "psycopg2 no está instalado. "
                    "Instala con: pip install psycopg2-binary o "
                    "poetry add psycopg2-binary"
                )
            
            # Conectar
            self._connect()
            
            # NO crear tabla - se crea con migración de Django
            # La tabla debe existir antes de usar el handler
            
            # Iniciar thread de escritura
            self._start_writer_thread()
            
        except Exception as e:
            print(f"Error al inicializar PostgreSQLHandler: {e}")
            print("IMPORTANTE: Asegúrate de haber ejecutado 'python manage.py migrate' para crear la tabla de logs")
            traceback.print_exc()
    
    def _connect(self) -> None:
        """Establece conexión con PostgreSQL."""
        try:
            self.connection = self.psycopg2.connect(
                self.config.connection_string
            )
            self.connection.autocommit = False
            self.connected = True
        except Exception as e:
            self.connected = False
            raise Exception(f"Error al conectar con PostgreSQL: {e}")
    
    def _create_table(self) -> None:
        """
        DEPRECATED: La tabla ahora se crea con migraciones de Django.
        
        Este método ya no se usa. La tabla 'application_logs' debe ser
        creada ejecutando: python manage.py migrate
        """
        # Este método ya no hace nada
        # La tabla se crea con la migración 0001_create_logs_table.py
        pass
    
    def _start_writer_thread(self) -> None:
        """Inicia el thread de escritura asíncrona."""
        self.running = True
        self.writer_thread = threading.Thread(
            target=self._writer_loop,
            daemon=True,
            name="PostgreSQLLogWriter"
        )
        self.writer_thread.start()
    
    def _writer_loop(self) -> None:
        """Loop principal del thread de escritura."""
        batch = []
        
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
            self.connection.rollback()
            self.connected = False
            self.logs_failed += len(batch)
            print(f"Error al escribir batch de logs: {e}")
    
    def _prepare_record(self, record: logging.LogRecord) -> tuple:
        """Prepara un LogRecord para inserción en PostgreSQL."""
        import socket
        
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
            exception = self.formatter.formatException(record.exc_info) if self.formatter else str(record.exc_info)
        
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
        """Emite un log record a la cola para escritura asíncrona."""
        try:
            self.log_queue.put_nowait(record)
        except queue.Full:
            try:
                self.log_queue.get_nowait()
                self.log_queue.put_nowait(record)
            except:
                pass
    
    def flush(self) -> None:
        """Fuerza la escritura de todos los logs pendientes."""
        self.log_queue.join()
    
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
        """Obtiene estadísticas del handler."""
        return {
            'logs_written': self.logs_written,
            'logs_failed': self.logs_failed,
            'queue_size': self.log_queue.qsize(),
            'connected': self.connected
        }
