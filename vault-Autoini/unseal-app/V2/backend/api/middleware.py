# api/middleware.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from core.password_manager import PasswordManager

logger = logging.getLogger(__name__)

class PasswordChangeMiddleware(BaseHTTPMiddleware):
    """
    Middleware que fuerza el cambio de contraseña temporal.
    """
    
    EXEMPT_PATHS = [
        "/api/auth/login",
        "/api/auth/password-status",
        "/api/auth/change-password",
        "/api/auth/update-password",  # ✅ AÑADIR ESTA RUTA
        "/api/health",
        "/api/health/live",
        "/api/health/ready",
        "/docs",
        "/openapi.json"
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Verificar si la ruta está exenta
        if any(request.url.path.startswith(path) for path in self.EXEMPT_PATHS):
            return await call_next(request)
        
        # Verificar autenticación
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)
        
        try:
            # Verificar si la contraseña es temporal
            pwd_manager = PasswordManager()
            is_temp = await pwd_manager.is_temporary_password()
            
            if is_temp:
                # La contraseña es temporal, rechazar la solicitud
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Temporary password must be changed",
                        "redirect": "/api/auth/password-status",
                        "message": "Debes cambiar tu contraseña temporal antes de continuar"
                    }
                )
            
        except Exception as e:
            logger.error(f"Error en middleware: {e}")
        
        return await call_next(request)