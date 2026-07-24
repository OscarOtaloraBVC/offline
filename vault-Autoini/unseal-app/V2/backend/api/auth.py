# api/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging
from typing import Optional  # ✅ Añadir Optional

from core.crypto import SecureKeyStore
from core.password_manager import PasswordManager  # ✅ Importar PasswordManager
from core.database import AsyncSessionLocal, SystemState  # ✅ Importar modelos
from sqlalchemy import select  # ✅ Importar select

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# ============================================
# CONFIGURACIÓN DESDE VARIABLES DE ENTORNO
# ============================================

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("❌ SECRET_KEY no está configurada en las variables de entorno")
logger.info(f"✅ SECRET_KEY configurada (longitud: {len(SECRET_KEY)})")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")

# ============================================
# GESTIÓN DE CONTRASEÑA CON PERSISTENCIA
# ============================================

def get_admin_password_hash() -> str:
    """Obtiene el hash de la BD o lo crea desde la variable de entorno"""
    keystore = SecureKeyStore()
    stored_hash = keystore.get_admin_password_hash()
    
    if stored_hash:
        logger.info("✅ Hash de admin obtenido desde la base de datos")
        return stored_hash
    
    # Primera ejecución: crear desde variable de entorno
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise ValueError("❌ ADMIN_PASSWORD no está configurada en las variables de entorno")
    
    admin_password = admin_password[:72] if len(admin_password) > 72 else admin_password
    new_hash = pwd_context.hash(admin_password)
    keystore.save_admin_password_hash(new_hash)
    logger.info("✅ Hash de admin creado desde variable de entorno y guardado en BD")
    return new_hash

ADMIN_PASSWORD_HASH = get_admin_password_hash()

# ============================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password = plain_password[:72] if len(plain_password) > 72 else plain_password
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error verificando contraseña: {e}")
        return False

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"username": username}
    except JWTError as e:
        logger.warning(f"Error decodificando token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ============================================
# MODELOS PYDANTIC
# ============================================

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class PasswordUpdateRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class PasswordStatusResponse(BaseModel):
    is_temporary: bool
    must_change: bool
    days_since_change: Optional[int] = None
    password_policy: dict

# ============================================
# ENDPOINTS DE AUTENTICACIÓN
# ============================================

@router.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    if login_data.username != ADMIN_USERNAME:
        logger.warning(f"Intento de login con usuario inválido: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    password = login_data.password[:72] if len(login_data.password) > 72 else login_data.password
    if not verify_password(password, ADMIN_PASSWORD_HASH):
        logger.warning(f"Intento de login con contraseña incorrecta para: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": login_data.username})
    logger.info(f"✅ Login exitoso para: {login_data.username}")
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/auth/verify")
async def verify_token(user: dict = Depends(get_current_user)):
    return {"valid": True, "username": user["username"]}

@router.post("/auth/update-password")
async def update_password(
    request: PasswordUpdateRequest,
    user: dict = Depends(get_current_user)
):
    global ADMIN_PASSWORD_HASH
    
    current_password = request.current_password[:72] if len(request.current_password) > 72 else request.current_password
    new_password = request.new_password[:72] if len(request.new_password) > 72 else request.new_password
    
    # 1. Verificar contraseña actual
    if not verify_password(current_password, ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña actual incorrecta"
        )
    
    keystore = SecureKeyStore()
    pwd_manager = PasswordManager()
    
    # 2. Guardar nuevo hash
    new_hash = pwd_context.hash(new_password)
    try:
        keystore.save_admin_password_hash(new_hash)
        ADMIN_PASSWORD_HASH = new_hash
        logger.info("✅ Nuevo hash de admin guardado en BD")
    except Exception as e:
        logger.error(f"❌ Error guardando nuevo hash en BD: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al guardar la nueva contraseña"
        )
    
    # 3. Marcar contraseña como cambiada
    try:
        await pwd_manager.mark_password_changed()
        logger.info("✅ Contraseña marcada como cambiada")
    except Exception as e:
        logger.error(f"❌ Error marcando contraseña como cambiada: {e}")
    
    # 4. Guardar en historial
    try:
        await pwd_manager.add_to_password_history(new_hash)
        logger.info("✅ Contraseña añadida al historial")
    except Exception as e:
        logger.error(f"❌ Error añadiendo al historial: {e}")
    
    # 5. ✅ SIEMPRE guardar la contraseña del worker (incluso si no hay llaves)
    try:
        # Guardar la contraseña en la BD para el worker
        keystore.save_unseal_password(new_password)
        logger.info("✅ Contraseña de unseal guardada en BD")
        
        # Intentar descifrar llaves con la nueva contraseña
        keys = keystore.get_keys(new_password)
        if keys:
            logger.info(f"✅ {len(keys)} llaves descifradas correctamente con nueva contraseña")
        else:
            logger.warning("⚠️ No se pudieron descifrar llaves con la nueva contraseña (puede que no haya llaves aún)")
        
        # Actualizar worker
        from main import monitor_worker
        if monitor_worker:
            monitor_worker.set_password(new_password)
            logger.info("✅ Worker actualizado con nueva contraseña")
    except Exception as e:
        logger.error(f"❌ Error sincronizando contraseña del worker: {e}")
        # No bloqueamos el cambio de contraseña
    
    logger.info("✅ Contraseña de admin actualizada correctamente")
    
    return {
        "message": "Contraseña actualizada correctamente",
        "success": True,
        "keys_available": False,
        "keys_decrypted": False
    }

@router.get("/auth/password-status", response_model=PasswordStatusResponse)
async def get_password_status(user: dict = Depends(get_current_user)):
    """Verifica si la contraseña actual es temporal"""
    pwd_manager = PasswordManager()
    is_temp = await pwd_manager.is_temporary_password()
    
    async with AsyncSessionLocal() as session:
        state = await session.execute(
            select(SystemState).where(SystemState.id == 1)
        )
        state = state.scalar_one_or_none()
        
        days_since = None
        if state and state.last_password_change:
            delta = datetime.utcnow() - state.last_password_change
            days_since = delta.days
    
    return PasswordStatusResponse(
        is_temporary=is_temp,
        must_change=is_temp,  # Si es temporal, debe cambiar
        days_since_change=days_since,
        password_policy={
            "min_length": 8,
            "max_length": 72,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special": True,
            "history_count": 5
        }
    )

@router.post("/auth/change-password")
async def change_password(
    request: PasswordChangeRequest,
    user: dict = Depends(get_current_user)
):
    """
    Cambia la contraseña del admin con validación completa.
    Este es el endpoint PRINCIPAL para cambio de contraseña.
    """
    try:
        pwd_manager = PasswordManager()
        keystore = SecureKeyStore()
        
        # 1. Validar contraseña actual
        current_hash = keystore.get_admin_password_hash()
        if not verify_password(request.current_password, current_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña actual incorrecta"
            )
        
        # 2. Validar nueva contraseña
        is_valid, msg = pwd_manager.validate_password_strength(request.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg
            )
        
        # 3. Verificar que coinciden
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Las contraseñas no coinciden"
            )
        
        # 4. Verificar que no es igual a la actual
        if request.new_password == request.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La nueva contraseña debe ser diferente a la actual"
            )
        
        # 5. Verificar historial (no reuso)
        new_hash = pwd_context.hash(request.new_password)
        if await pwd_manager.check_password_reuse(new_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta contraseña ya fue usada anteriormente"
            )
        
        # 6. RE-CIFRAR TODAS LAS LLAVES
        logger.info("🔐 Re-cifrando todas las llaves con nueva contraseña...")
        reencrypt_success = await pwd_manager.reencrypt_all_keys(
            request.current_password,
            request.new_password
        )
        
        if not reencrypt_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error re-cifrando llaves. La contraseña no se cambió."
            )
        
        # 7. Guardar nuevo hash
        keystore.save_admin_password_hash(new_hash)
        global ADMIN_PASSWORD_HASH
        ADMIN_PASSWORD_HASH = new_hash
        
        # 8. Marcar como cambiada
        await pwd_manager.mark_password_changed()
        
        # 9. Guardar en historial
        await pwd_manager.add_to_password_history(new_hash)
        
        # 10. Actualizar worker (ya se hizo en reencrypt_all_keys)
        from main import monitor_worker
        if monitor_worker:
            monitor_worker.set_password(request.new_password)
            logger.info("✅ Worker actualizado con nueva contraseña")
        
        # 11. Invalidar tokens antiguos (opcional)
        # Se podría implementar blacklist de tokens
        
        logger.info(f"✅ Contraseña cambiada exitosamente para {user['username']}")
        
        return {
            "success": True,
            "message": "Contraseña cambiada exitosamente",
            "keys_reencrypted": True,
            "temporary_password_reset": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error cambiando contraseña: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )