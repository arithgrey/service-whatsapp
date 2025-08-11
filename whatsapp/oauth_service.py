"""
Servicio de integración con OAuth
Siguiendo las reglas del backend: integración obligatoria con service-oauth
"""

import requests
import logging
from django.conf import settings
from app.middleware import api_circuit_breaker

logger = logging.getLogger(__name__)

class OAuthService:
    """Servicio para integrar con service-oauth"""
    
    def __init__(self):
        self.base_url = settings.OAUTH_SERVICE_URL
        self.timeout = 10
    
    @api_circuit_breaker
    def verify_token(self, token):
        """Verificar token JWT con service-oauth"""
        try:
            url = f"{self.base_url}/api/verify-token/"
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error verificando token: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error en verificación de token: {str(e)}")
            raise
    
    @api_circuit_breaker
    def get_user_profile(self, token):
        """Obtener perfil de usuario del service-oauth"""
        try:
            url = f"{self.base_url}/api/user/profile/"
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error obteniendo perfil: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo perfil: {str(e)}")
            raise
    
    @api_circuit_breaker
    def validate_permission(self, token, permission):
        """Validar permiso específico del usuario"""
        try:
            url = f"{self.base_url}/api/user/validate-permission/"
            headers = {'Authorization': f'Bearer {token}'}
            data = {'permission': permission}
            
            response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json().get('has_permission', False)
            else:
                logger.error(f"Error validando permiso: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error validando permiso: {str(e)}")
            raise

# Instancia global del servicio
oauth_service = OAuthService() 