"""
Middleware para logging de integraciones con sistemas externos.

Este middleware captura automáticamente todas las peticiones a endpoints
de integración (ERPs, APIs externas, webhooks, servicios de terceros)
y registra información detallada usando el sistema de logging personalizado.

Características:
- Logging estructurado de requests y responses
- Captura automática de errores con traceback completo
- Medición de tiempos de respuesta
- Contexto enriquecido para debugging
- Soporte para múltiples tipos de integración
- Campos JSONB para búsquedas avanzadas en PostgreSQL
"""

import json
import time
from django.utils.deprecation import MiddlewareMixin
from django_advanced_logging import get_logger


class ExternalIntegrationLoggingMiddleware(MiddlewareMixin):
    """
    Middleware que registra todas las peticiones a endpoints de integración externa.
    
    Rutas monitoreadas (configurable en settings.py):
    - /api/erp/*          - Integraciones con ERPs (SAP, Oracle, etc.)
    - /api/integrations/* - Integraciones genéricas
    - /api/external/*     - APIs externas
    - /webhook/*          - Webhooks entrantes
    - /api/payment/*      - Procesadores de pago (Stripe, PayPal, etc.)
    - /api/shipping/*     - APIs de envío (FedEx, DHL, etc.)
    - /api/crm/*          - CRMs (Salesforce, HubSpot, etc.)
    - /api/email/*        - Servicios de email
    - /api/sms/*          - Servicios de SMS
    - /api/notification/* - Servicios de notificaciones
    
    Uso en settings.py:
        MIDDLEWARE = [
            ...
            'django_advanced_logging.django.middleware.ExternalIntegrationLoggingMiddleware',
        ]
        
        # Opcional: Personalizar rutas monitoreadas
        INTEGRATION_MONITORED_PATHS = [
            '/api/erp/',
            '/api/custom/',
        ]
        
        # Opcional: Personalizar tipos de integración
        INTEGRATION_TYPES = {
            '/api/erp/': 'erp',
            '/api/custom/': 'custom_system',
        }
    """
    
    # Configuración por defecto de rutas a monitorear
    DEFAULT_MONITORED_PATHS = [
        '/api/erp/',
        '/api/integrations/',
        '/api/external/',
        '/webhook/',
        '/api/payment/',
        '/api/shipping/',
        '/api/crm/',
        '/api/email/',
        '/api/sms/',
        '/api/notification/',
        '/api/magento/',
        '/api/ecommerce/',
    ]
    
    # Mapeo por defecto de rutas a tipos de integración
    DEFAULT_INTEGRATION_TYPES = {
        '/api/erp/': 'erp',
        '/api/integrations/': 'generic',
        '/api/external/': 'external_api',
        '/webhook/': 'webhook',
        '/api/payment/': 'payment_processor',
        '/api/shipping/': 'shipping_provider',
        '/api/crm/': 'crm',
        '/api/email/': 'email_service',
        '/api/sms/': 'sms_service',
        '/api/notification/': 'notification_service',
        '/api/magento/': 'magento',
        '/api/ecommerce/': 'ecommerce',
    }
    
    def __init__(self, get_response):
        """
        Inicializa el middleware.
        
        Args:
            get_response: Callable que procesa el request
        """
        self.get_response = get_response
        super().__init__(get_response)
        
        # Logger específico para integraciones externas
        self.logger = get_logger('external_integrations')
        
        # Cargar configuración desde settings
        from django.conf import settings
        self.monitored_paths = getattr(
            settings, 
            'INTEGRATION_MONITORED_PATHS', 
            self.DEFAULT_MONITORED_PATHS
        )
        self.integration_types = getattr(
            settings,
            'INTEGRATION_TYPES',
            self.DEFAULT_INTEGRATION_TYPES
        )
    
    def __call__(self, request):
        """
        Procesa cada request y response.
        
        Args:
            request: HttpRequest object
            
        Returns:
            HttpResponse object
        """
        # Solo procesar rutas de integración
        if not self._is_integration_endpoint(request.path):
            return self.get_response(request)
        
        # Identificar tipo de integración
        integration_type = self._get_integration_type(request.path)
        
        # Capturar tiempo de inicio
        start_time = time.time()
        
        # Extraer información del request
        request_info = self._extract_request_info(request, integration_type)
        
        # Log del request entrante
        self.logger.info(
            f"[{integration_type.upper()}] Request recibido: {request.method} {request.path}",
            extra={'extra_fields': request_info}
        )
        
        try:
            # Procesar el request
            response = self.get_response(request)
            
            # Calcular tiempo de respuesta
            duration = time.time() - start_time
            
            # Determinar nivel de log según status code
            log_level = self._get_log_level(response.status_code)
            
            # Preparar información del response
            response_info = {
                **request_info,
                'status_code': response.status_code,
                'duration_seconds': round(duration, 3),
                'success': 200 <= response.status_code < 300,
            }
            
            # Log del response
            log_message = (
                f"[{integration_type.upper()}] Response: "
                f"{response.status_code} - {duration:.3f}s"
            )
            
            getattr(self.logger, log_level)(
                log_message,
                extra={'extra_fields': response_info}
            )
            
            return response
            
        except Exception as e:
            # Calcular tiempo hasta el error
            duration = time.time() - start_time
            
            # Extraer contexto específico del error
            error_context = self._extract_error_context(request, e, integration_type)
            
            # Preparar información completa del error
            error_info = {
                **request_info,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'duration_seconds': round(duration, 3),
                **error_context,
            }
            
            # Log del error con traceback completo
            self.logger.error(
                f"[{integration_type.upper()}] Error en integración: "
                f"{type(e).__name__} - {str(e)}",
                extra={'extra_fields': error_info},
                exc_info=True  # Incluye traceback completo
            )
            
            # Re-lanzar la excepción para que Django la maneje
            raise
    
    def process_exception(self, request, exception):
        """
        Procesa excepciones no manejadas en endpoints de integración.
        
        Este método es llamado por Django cuando ocurre una excepción
        que no fue capturada en el código de la vista.
        
        Args:
            request: HttpRequest object
            exception: La excepción que ocurrió
            
        Returns:
            None (permite que Django maneje la excepción normalmente)
        """
        if not self._is_integration_endpoint(request.path):
            return None
        
        integration_type = self._get_integration_type(request.path)
        
        # Log crítico de excepción no manejada
        self.logger.critical(
            f"[{integration_type.upper()}] Excepción NO MANEJADA: {exception}",
            extra={
                'extra_fields': {
                    'path': request.path,
                    'method': request.method,
                    'integration_type': integration_type,
                    'exception_type': type(exception).__name__,
                    'exception_message': str(exception),
                    'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                }
            },
            exc_info=True
        )
        
        # Retornar None para que Django continúe con el manejo normal
        return None
    
    def _is_integration_endpoint(self, path):
        """
        Determina si una ruta es un endpoint de integración.
        
        Args:
            path (str): La ruta del request
            
        Returns:
            bool: True si es un endpoint de integración
        """
        return any(pattern in path for pattern in self.monitored_paths)
    
    def _get_integration_type(self, path):
        """
        Determina el tipo de integración basado en la ruta.
        
        Args:
            path (str): La ruta del request
            
        Returns:
            str: Tipo de integración
        """
        for pattern, integration_type in self.integration_types.items():
            if pattern in path:
                return integration_type
        return 'unknown'
    
    def _extract_request_info(self, request, integration_type):
        """
        Extrae información relevante del request.
        
        La información extraída se guarda en JSONB para permitir
        búsquedas avanzadas en PostgreSQL.
        
        Args:
            request: HttpRequest object
            integration_type (str): Tipo de integración
            
        Returns:
            dict: Información estructurada del request
        """
        # Información base
        info = {
            'integration_type': integration_type,
            'path': request.path,
            'method': request.method,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'request_id': request.headers.get('X-Request-ID', 'not-provided'),
            'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
        }
        
        # Headers específicos según tipo de integración
        if integration_type == 'erp':
            info.update({
                'client_id': request.headers.get('X-Client-ID', 'unknown'),
                'erp_system': request.headers.get('X-ERP-System', 'unknown'),
                'api_version': request.headers.get('X-API-Version', 'v1'),
            })
        
        elif integration_type == 'payment_processor':
            info.update({
                'provider': request.headers.get('X-Payment-Provider', 'unknown'),
                'transaction_id': request.headers.get('X-Transaction-ID', 'unknown'),
            })
        
        elif integration_type == 'shipping_provider':
            info.update({
                'carrier': request.headers.get('X-Carrier', 'unknown'),
                'tracking_number': request.headers.get('X-Tracking-Number', 'unknown'),
            })
        
        elif integration_type == 'crm':
            info.update({
                'crm_system': request.headers.get('X-CRM-System', 'unknown'),
                'account_id': request.headers.get('X-Account-ID', 'unknown'),
            })
        
        elif integration_type == 'webhook':
            signature = request.headers.get('X-Signature', 'not-provided')
            info.update({
                'webhook_source': request.headers.get('X-Webhook-Source', 'unknown'),
                'event_type': request.headers.get('X-Event-Type', 'unknown'),
                'signature_provided': signature != 'not-provided',
                # Truncar signature por seguridad
                'signature_preview': signature[:20] + '...' if len(signature) > 20 else signature,
            })
        
        elif integration_type in ['email_service', 'sms_service', 'notification_service']:
            info.update({
                'service_provider': request.headers.get('X-Service-Provider', 'unknown'),
                'message_id': request.headers.get('X-Message-ID', 'unknown'),
            })

        elif integration_type == 'magento':
            info.update({
            # Autenticación y autorización
            'store_code': request.headers.get('Store', 'default'),
            'store_view': request.headers.get('X-Store-View', 'default'),
            'authorization_type': 'Bearer' if 'Authorization' in request.headers else 'None',
            
            # Identificación de la tienda/cliente
            'magento_version': request.headers.get('X-Magento-Version', 'unknown'),
            'integration_name': request.headers.get('X-Integration-Name', 'unknown'),
            
            # Rate limiting y control
            'rate_limit_remaining': request.headers.get('X-RateLimit-Remaining', 'unknown'),
            'rate_limit_reset': request.headers.get('X-RateLimit-Reset', 'unknown'),
            
            # Tracking
            'request_id': request.headers.get('X-Request-ID', 'not-provided'),
            'correlation_id': request.headers.get('X-Correlation-ID', 'not-provided'),
        })
        
        else:  # generic, external_api, unknown
            info.update({
                'service': request.headers.get('X-Service', 'unknown'),
                'client_id': request.headers.get('X-Client-ID', 'unknown'),
            })
        
        # Query parameters
        if request.GET:
            info['query_params'] = dict(request.GET)
        
        # Tamaño del body
        if request.body:
            info['body_size_bytes'] = len(request.body)
            
            # Para webhooks, intentar extraer evento del body
            if integration_type == 'webhook' and info.get('event_type') == 'unknown':
                try:
                    body_data = json.loads(request.body)
                    info['event_type'] = body_data.get('type', body_data.get('event', 'unknown'))
                except:
                    pass
        
        # Content-Type
        info['content_type'] = request.content_type
        
        return info
    
    def _extract_error_context(self, request, exception, integration_type):
        """
        Extrae contexto adicional específico del error.
        
        Args:
            request: HttpRequest object
            exception: La excepción que ocurrió
            integration_type (str): Tipo de integración
            
        Returns:
            dict: Contexto adicional del error
        """
        context = {
            'exception_class': exception.__class__.__module__ + '.' + exception.__class__.__name__,
        }
        
        # Intentar extraer información del body según el tipo
        try:
            if request.body:
                body_data = json.loads(request.body)
                
                if integration_type == 'payment_processor':
                    context.update({
                        'payment_amount': body_data.get('amount'),
                        'payment_currency': body_data.get('currency'),
                        'payment_method': body_data.get('payment_method'),
                    })
                
                elif integration_type == 'shipping_provider':
                    context.update({
                        'shipping_origin': body_data.get('origin'),
                        'shipping_destination': body_data.get('destination'),
                        'package_count': len(body_data.get('packages', [])),
                    })
                
                elif integration_type == 'erp':
                    context.update({
                        'order_number': body_data.get('order_number'),
                        'customer_id': body_data.get('customer_id'),
                        'action': body_data.get('action'),
                    })
                
                elif integration_type == 'webhook':
                    context.update({
                        'webhook_id': body_data.get('id'),
                        'webhook_data_keys': list(body_data.keys()) if isinstance(body_data, dict) else None,
                    })

                if integration_type == 'maagento':
                    context = self._extract_magento_context(request)
                    
        except Exception:
            # Si no se puede parsear, no agregar contexto del body
            pass
        
        return context

    def _extract_magento_context(self, request):
        """
        Extrae contexto específico de operaciones con Magento.
        
        Args:
            request: HttpRequest object
            
        Returns:
            dict: Contexto adicional de Magento
        """
        context = {}
        
        try:
            if request.body:
                body_data = json.loads(request.body)
                
                # Identificar el tipo de operación por la ruta
                path = request.path
                
                # ============================================================
                # PRODUCTOS
                # ============================================================
                if '/products' in path:
                    context.update({
                        'operation': 'product_management',
                        'sku': body_data.get('product', {}).get('sku'),
                        'product_name': body_data.get('product', {}).get('name'),
                        'product_type': body_data.get('product', {}).get('type_id'),  # simple, configurable, bundle, etc.
                        'attribute_set_id': body_data.get('product', {}).get('attribute_set_id'),
                        'status': body_data.get('product', {}).get('status'),  # 1=enabled, 2=disabled
                        'visibility': body_data.get('product', {}).get('visibility'),  # 1-4
                        'price': body_data.get('product', {}).get('price'),
                        'categories': body_data.get('product', {}).get('category_ids', []),
                    })
                
                # ============================================================
                # ÓRDENES (ORDERS)
                # ============================================================
                elif '/orders' in path:
                    order = body_data.get('entity', body_data)
                    
                    context.update({
                        'operation': 'order_management',
                        'order_id': order.get('entity_id'),
                        'increment_id': order.get('increment_id'),  # Número de orden visible
                        'order_status': order.get('status'),  # pending, processing, complete, etc.
                        'order_state': order.get('state'),  # new, processing, complete, closed, canceled
                        'grand_total': order.get('grand_total'),
                        'subtotal': order.get('subtotal'),
                        'tax_amount': order.get('tax_amount'),
                        'shipping_amount': order.get('shipping_amount'),
                        'discount_amount': order.get('discount_amount'),
                        'currency_code': order.get('order_currency_code'),
                        'customer_email': order.get('customer_email'),
                        'customer_id': order.get('customer_id'),
                        'items_count': len(order.get('items', [])),
                        'payment_method': order.get('payment', {}).get('method'),
                        'shipping_method': order.get('shipping_method'),
                        'store_id': order.get('store_id'),
                    })
                
                # ============================================================
                # INVENTARIO (STOCK)
                # ============================================================
                elif '/stockItems' in path or '/inventory' in path:
                    stock_item = body_data.get('stockItem', body_data)
                    
                    context.update({
                        'operation': 'inventory_management',
                        'sku': stock_item.get('sku') or body_data.get('sku'),
                        'product_id': stock_item.get('product_id'),
                        'qty': stock_item.get('qty'),
                        'is_in_stock': stock_item.get('is_in_stock'),
                        'manage_stock': stock_item.get('manage_stock'),
                        'min_qty': stock_item.get('min_qty'),
                        'max_sale_qty': stock_item.get('max_sale_qty'),
                        'backorders': stock_item.get('backorders'),
                    })
                
                # ============================================================
                # CLIENTES (CUSTOMERS)
                # ============================================================
                elif '/customers' in path:
                    customer = body_data.get('customer', body_data)
                    
                    context.update({
                        'operation': 'customer_management',
                        'customer_id': customer.get('id'),
                        'email': customer.get('email'),
                        'firstname': customer.get('firstname'),
                        'lastname': customer.get('lastname'),
                        'group_id': customer.get('group_id'),
                        'store_id': customer.get('store_id'),
                        'website_id': customer.get('website_id'),
                        'addresses_count': len(customer.get('addresses', [])),
                    })
                
                # ============================================================
                # CARRITOS (CARTS/QUOTES)
                # ============================================================
                elif '/carts' in path or '/quote' in path:
                    cart = body_data.get('cart', body_data)
                    
                    context.update({
                        'operation': 'cart_management',
                        'cart_id': cart.get('id'),
                        'customer_id': cart.get('customer', {}).get('id'),
                        'customer_email': cart.get('customer', {}).get('email'),
                        'items_count': cart.get('items_count'),
                        'items_qty': cart.get('items_qty'),
                        'is_active': cart.get('is_active'),
                        'store_id': cart.get('store_id'),
                    })
                
                # ============================================================
                # CATEGORÍAS
                # ============================================================
                elif '/categories' in path:
                    category = body_data.get('category', body_data)
                    
                    context.update({
                        'operation': 'category_management',
                        'category_id': category.get('id'),
                        'category_name': category.get('name'),
                        'parent_id': category.get('parent_id'),
                        'level': category.get('level'),
                        'is_active': category.get('is_active'),
                        'product_count': category.get('product_count'),
                    })
                
                # ============================================================
                # FACTURAS (INVOICES)
                # ============================================================
                elif '/invoices' in path:
                    invoice = body_data.get('entity', body_data)
                    
                    context.update({
                        'operation': 'invoice_management',
                        'invoice_id': invoice.get('entity_id'),
                        'increment_id': invoice.get('increment_id'),
                        'order_id': invoice.get('order_id'),
                        'state': invoice.get('state'),  # 1=pending, 2=paid, 3=canceled
                        'grand_total': invoice.get('grand_total'),
                        'store_id': invoice.get('store_id'),
                    })
                
                # ============================================================
                # ENVÍOS (SHIPMENTS)
                # ============================================================
                elif '/shipment' in path:
                    shipment = body_data.get('entity', body_data)
                    
                    context.update({
                        'operation': 'shipment_management',
                        'shipment_id': shipment.get('entity_id'),
                        'increment_id': shipment.get('increment_id'),
                        'order_id': shipment.get('order_id'),
                        'total_qty': shipment.get('total_qty'),
                        'packages_count': len(shipment.get('packages', [])),
                        'tracks_count': len(shipment.get('tracks', [])),
                    })
                
                # ============================================================
                # REEMBOLSOS (CREDIT MEMOS)
                # ============================================================
                elif '/creditmemo' in path:
                    creditmemo = body_data.get('entity', body_data)
                    
                    context.update({
                        'operation': 'refund_management',
                        'creditmemo_id': creditmemo.get('entity_id'),
                        'increment_id': creditmemo.get('increment_id'),
                        'order_id': creditmemo.get('order_id'),
                        'state': creditmemo.get('state'),
                        'grand_total': creditmemo.get('grand_total'),
                        'adjustment': creditmemo.get('adjustment'),
                    })
                
                # ============================================================
                # WEBHOOKS DE MAGENTO
                # ============================================================
                elif 'webhook' in path.lower():
                    context.update({
                        'operation': 'webhook',
                        'event_type': body_data.get('event_type') or body_data.get('topic'),
                        'entity_type': body_data.get('entity_type'),
                        'entity_id': body_data.get('entity_id'),
                        'store_id': body_data.get('store_id'),
                        'created_at': body_data.get('created_at'),
                    })
                
        except json.JSONDecodeError:
            context['parse_error'] = 'Invalid JSON body'
        except Exception as e:
            context['extraction_error'] = str(e)
        
        return context
    
    def _get_client_ip(self, request):
        """
        Obtiene la IP real del cliente, considerando proxies.
        
        Args:
            request: HttpRequest object
            
        Returns:
            str: Dirección IP del cliente
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _get_log_level(self, status_code):
        """
        Determina el nivel de log según el status code HTTP.
        
        Args:
            status_code (int): Código de estado HTTP
            
        Returns:
            str: Nivel de log ('info', 'warning', 'error')
        """
        if 200 <= status_code < 300:
            return 'info'
        elif 300 <= status_code < 400:
            return 'info'
        elif 400 <= status_code < 500:
            return 'warning'
        else:  # 500+
            return 'error'