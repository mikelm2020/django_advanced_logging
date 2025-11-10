"""
Migración para crear tabla de logs de PostgreSQL.

Esta migración crea la tabla 'application_logs' que será usada
por el PostgreSQLHandler para almacenar logs de forma asíncrona.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Primera migración - Crea tabla de logs.
    """
    
    initial = True
    
    dependencies = []
    
    operations = [
        migrations.RunSQL(
            sql="""
            -- Crear tabla de logs
            CREATE TABLE IF NOT EXISTS application_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                level VARCHAR(10) NOT NULL,
                logger_name VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                module VARCHAR(100),
                function VARCHAR(100),
                line_number INTEGER,
                thread_id BIGINT,
                thread_name VARCHAR(100),
                process_id INTEGER,
                exception TEXT,
                extra_data JSONB,
                environment VARCHAR(50),
                hostname VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Crear índices para mejor performance
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp 
                ON application_logs(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_logs_level 
                ON application_logs(level);
            CREATE INDEX IF NOT EXISTS idx_logs_logger 
                ON application_logs(logger_name);
            CREATE INDEX IF NOT EXISTS idx_logs_environment 
                ON application_logs(environment);
            CREATE INDEX IF NOT EXISTS idx_logs_extra_data 
                ON application_logs USING GIN(extra_data);
            
            -- Comentarios descriptivos
            COMMENT ON TABLE application_logs IS 
                'Logs de aplicación generados por django-advanced-logging';
            COMMENT ON COLUMN application_logs.extra_data IS 
                'Campos personalizados en formato JSONB para búsquedas avanzadas';
            """,
            
            reverse_sql="""
            -- Eliminar tabla de logs
            DROP TABLE IF EXISTS application_logs CASCADE;
            """
        ),
    ]