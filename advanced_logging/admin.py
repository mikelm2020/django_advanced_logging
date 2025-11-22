"""
Admin para Advanced Logging.

Proporciona una interfaz de administracion para visualizar
y filtrar logs de la aplicacion.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count

from .models import ApplicationLog


@admin.register(ApplicationLog)
class ApplicationLogAdmin(admin.ModelAdmin):
    """Admin para visualizar logs de la aplicacion."""

    list_display = [
        'colored_level',
        'timestamp',
        'logger_name',
        'short_message',
        'module',
        'function',
        'environment',
        'has_exception_icon',
    ]

    list_filter = [
        'level',
        'environment',
        'logger_name',
        ('timestamp', admin.DateFieldListFilter),
    ]

    search_fields = [
        'message',
        'logger_name',
        'module',
        'function',
        'exception',
    ]

    readonly_fields = [
        'timestamp',
        'level',
        'logger_name',
        'message',
        'module',
        'function',
        'line_number',
        'thread_id',
        'thread_name',
        'process_id',
        'exception_formatted',
        'extra_data_formatted',
        'environment',
        'hostname',
        'created_at',
    ]

    fieldsets = (
        ('Informacion Principal', {
            'fields': (
                'timestamp',
                'level',
                'logger_name',
                'message',
                'environment',
            )
        }),
        ('Ubicacion del Codigo', {
            'fields': (
                'module',
                'function',
                'line_number',
            ),
            'classes': ('collapse',),
        }),
        ('Informacion del Proceso', {
            'fields': (
                'thread_id',
                'thread_name',
                'process_id',
                'hostname',
            ),
            'classes': ('collapse',),
        }),
        ('Excepcion', {
            'fields': ('exception_formatted',),
            'classes': ('collapse',),
        }),
        ('Datos Extra', {
            'fields': ('extra_data_formatted',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

    list_per_page = 50

    def has_add_permission(self, request):
        """No permitir agregar logs manualmente."""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar logs."""
        return False

    def colored_level(self, obj):
        """Muestra el nivel con color."""
        colors = {
            'DEBUG': '#17a2b8',    # Cyan
            'INFO': '#28a745',     # Green
            'WARNING': '#ffc107',  # Yellow
            'ERROR': '#dc3545',    # Red
            'CRITICAL': '#6f42c1', # Purple
        }
        color = colors.get(obj.level, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.level
        )
    colored_level.short_description = 'Nivel'
    colored_level.admin_order_field = 'level'

    def short_message(self, obj):
        """Muestra mensaje truncado."""
        max_length = 80
        if len(obj.message) > max_length:
            return f"{obj.message[:max_length]}..."
        return obj.message
    short_message.short_description = 'Mensaje'

    def has_exception_icon(self, obj):
        """Muestra icono si tiene excepcion."""
        if obj.exception:
            return format_html(
                '<span style="color: #dc3545;" title="Tiene excepcion">&#9888;</span>'
            )
        return ''
    has_exception_icon.short_description = 'Exc'

    def exception_formatted(self, obj):
        """Muestra la excepcion formateada."""
        if not obj.exception:
            return "Sin excepcion"
        return format_html(
            '<pre style="white-space: pre-wrap; font-family: monospace; '
            'background: #f8f9fa; padding: 10px; border-radius: 4px;">{}</pre>',
            obj.exception
        )
    exception_formatted.short_description = 'Excepcion'

    def extra_data_formatted(self, obj):
        """Muestra los datos extra formateados."""
        if not obj.extra_data:
            return "Sin datos extra"

        import json
        formatted = json.dumps(obj.extra_data, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="white-space: pre-wrap; font-family: monospace; '
            'background: #f8f9fa; padding: 10px; border-radius: 4px;">{}</pre>',
            formatted
        )
    extra_data_formatted.short_description = 'Datos Extra'

    def get_queryset(self, request):
        """Optimiza las queries."""
        return super().get_queryset(request).defer('exception', 'extra_data')

    class Media:
        css = {
            'all': []
        }
