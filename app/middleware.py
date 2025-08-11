"""
Middleware para Circuit Breaker Pattern
Siguiendo las reglas del backend: implementación obligatoria de Circuit Breaker
"""

import pybreaker
from django.http import JsonResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Circuit breaker para llamadas a APIs externas
api_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=5,  # Número máximo de fallos antes de abrir el circuito
    reset_timeout=60,  # Tiempo en segundos antes de intentar cerrar el circuito
    exclude=[Exception]  # Excepciones que no cuentan como fallos
)

# Función de fallback
def default_fallback(func, *args, **kwargs):
    """Función de fallback cuando el circuito está abierto"""
    logger.warning(f"Circuit Breaker OPEN - Fallback para función: {func.__name__}")
    return {
        "status": "service_unavailable", 
        "message": "Servicio temporalmente no disponible",
        "circuit_state": "OPEN"
    }

# Configurar fallback
api_circuit_breaker.fallback_function = default_fallback

class CircuitBreakerMiddleware:
    """Middleware para verificar estado del Circuit Breaker"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar estado del circuito antes de procesar
        if api_circuit_breaker.current_state == pybreaker.STATE_OPEN:
            logger.warning("Circuit Breaker OPEN - Rechazando request")
            return JsonResponse({
                'error': 'Service temporarily unavailable',
                'circuit_state': 'OPEN',
                'message': 'El servicio está temporalmente no disponible'
            }, status=503)
        
        response = self.get_response(request)
        return response

class CircuitBreakerLoggingMiddleware:
    """Middleware para logging del Circuit Breaker"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log del estado del circuito
        logger.info(f"Circuit Breaker State: {api_circuit_breaker.current_state}")
        
        response = self.get_response(request)
        return response 