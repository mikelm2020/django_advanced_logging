"""
Migracion inicial para Advanced Logging.

Crea la tabla de logs con todos los campos necesarios e indices
optimizados para consultas frecuentes.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Primera migracion - Crea tabla de logs."""

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ApplicationLog',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('timestamp', models.DateTimeField(
                    db_index=True,
                    help_text='Momento en que se genero el log',
                    verbose_name='Timestamp'
                )),
                ('level', models.CharField(
                    choices=[
                        ('DEBUG', 'Debug'),
                        ('INFO', 'Info'),
                        ('WARNING', 'Warning'),
                        ('ERROR', 'Error'),
                        ('CRITICAL', 'Critical')
                    ],
                    db_index=True,
                    help_text='Nivel de severidad del log',
                    max_length=10,
                    verbose_name='Nivel'
                )),
                ('logger_name', models.CharField(
                    db_index=True,
                    help_text='Nombre del logger que genero el log',
                    max_length=255,
                    verbose_name='Logger'
                )),
                ('message', models.TextField(
                    help_text='Mensaje del log',
                    verbose_name='Mensaje'
                )),
                ('module', models.CharField(
                    blank=True,
                    help_text='Modulo Python donde se genero el log',
                    max_length=100,
                    null=True,
                    verbose_name='Modulo'
                )),
                ('function', models.CharField(
                    blank=True,
                    help_text='Funcion donde se genero el log',
                    max_length=100,
                    null=True,
                    verbose_name='Funcion'
                )),
                ('line_number', models.IntegerField(
                    blank=True,
                    help_text='Linea de codigo donde se genero el log',
                    null=True,
                    verbose_name='Linea'
                )),
                ('thread_id', models.BigIntegerField(
                    blank=True,
                    null=True,
                    verbose_name='Thread ID'
                )),
                ('thread_name', models.CharField(
                    blank=True,
                    max_length=100,
                    null=True,
                    verbose_name='Thread'
                )),
                ('process_id', models.IntegerField(
                    blank=True,
                    null=True,
                    verbose_name='Process ID'
                )),
                ('exception', models.TextField(
                    blank=True,
                    help_text='Traceback si hubo una excepcion',
                    null=True,
                    verbose_name='Excepcion'
                )),
                ('extra_data', models.JSONField(
                    blank=True,
                    help_text='Campos personalizados en formato JSON',
                    null=True,
                    verbose_name='Datos Extra'
                )),
                ('environment', models.CharField(
                    blank=True,
                    db_index=True,
                    help_text='Entorno de ejecucion',
                    max_length=50,
                    null=True,
                    verbose_name='Entorno'
                )),
                ('hostname', models.CharField(
                    blank=True,
                    help_text='Nombre del servidor',
                    max_length=255,
                    null=True,
                    verbose_name='Servidor'
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    help_text='Momento de insercion en la base de datos',
                    verbose_name='Creado'
                )),
            ],
            options={
                'verbose_name': 'Log de Aplicacion',
                'verbose_name_plural': 'Logs de Aplicacion',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='applicationlog',
            index=models.Index(
                fields=['-timestamp'],
                name='advanced_lo_timesta_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='applicationlog',
            index=models.Index(
                fields=['level'],
                name='advanced_lo_level_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='applicationlog',
            index=models.Index(
                fields=['logger_name'],
                name='advanced_lo_logger__idx'
            ),
        ),
        migrations.AddIndex(
            model_name='applicationlog',
            index=models.Index(
                fields=['environment'],
                name='advanced_lo_environ_idx'
            ),
        ),
    ]
