import os
import secrets
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# Configuración de seguridad
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "480"))

# Contexto de hash de contraseñas
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# Usuario admin desde variables de entorno
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = pwd_context.hash(os.getenv("ADMIN_PASSWORD", "admin123"))

class SecurityService:
    """Servicio de seguridad para autenticación y autorización"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica una contraseña contra su hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verificando contraseña: {e}")
            return False
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Genera hash de una contraseña"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crea un token JWT de acceso"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_access_token(token: str) -> dict:
        """Decodifica un token JWT"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"Error decodificando token: {e}")
            raise
    
    @staticmethod
    def validate_admin_credentials(username: str, password: str) -> bool:
        """Valida las credenciales del administrador"""
        if username != ADMIN_USERNAME:
            return False
        return SecurityService.verify_password(password, ADMIN_PASSWORD_HASH)
    
    @staticmethod
    def update_admin_password(new_password: str) -> bool:
        """Actualiza la contraseña del administrador"""
        global ADMIN_PASSWORD_HASH
        try:
            ADMIN_PASSWORD_HASH = SecurityService.get_password_hash(new_password)
            # En producción, deberías persistir esto en la base de datos o en un secret
            logger.info("Contraseña de admin actualizada")
            return True
        except Exception as e:
            logger.error(f"Error actualizando contraseña: {e}")
            return False
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Genera un token seguro aleatorio"""
        return secrets.token_urlsafe(length)

# Funciones de utilidad para rate limiting (opcional)
class RateLimiter:
    """Rate limiter simple en memoria"""
    
    def __init__(self, max_requests: int = 5, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Verifica si el cliente puede hacer una request"""
        import time
        
        now = time.time()
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Limpiar requests antiguas
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.time_window
        ]
        
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        self.requests[client_id].append(now)
        return True

# Funciones para auditoría (placeholder)
class AuditLogger:
    """Logger de auditoría para eventos de seguridad"""
    
    @staticmethod
    def log_event(event_type: str, user: str, details: dict):
        """Registra un evento de auditoría"""
        import json
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user": user,
            "details": details
        }
        
        # En producción, enviar a un sistema de logging centralizado
        logger.info(f"AUDIT: {json.dumps(log_entry)}")