# backend/api/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

from core.crypto import SecureKeyStore

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
    """
    Actualiza la contraseña del admin y sincroniza con las llaves.
    
    Flujo:
    1. Verificar contraseña actual
    2. Probar si la nueva contraseña puede descifrar las llaves
    3. Guardar nuevo hash en BD
    4. Si las llaves se descifran, actualizar contraseña de unseal
    5. Si NO se descifran, re-cifrar las llaves con la nueva contraseña
    """
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
    
    # 2. Probar si la nueva contraseña puede descifrar las llaves
    keys_decrypted = False
    keys_count = 0
    
    try:
        existing_keys = keystore.get_keys(current_password)
        keys_count = len(existing_keys)
        
        if existing_keys:
            # Verificar si la nueva contraseña puede descifrar las llaves
            try:
                test_keys = keystore.get_keys(new_password)
                if test_keys:
                    keys_decrypted = True
                    logger.info(f"✅ La nueva contraseña puede descifrar {len(test_keys)} llaves")
                else:
                    logger.info("🔄 La nueva contraseña NO puede descifrar las llaves. Re-cifrando...")
                    # Re-cifrar las llaves con la nueva contraseña
                    success = keystore.reencrypt_keys(current_password, new_password)
                    if success:
                        logger.info("✅ Llaves re-cifradas correctamente con la nueva contraseña")
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error al re-cifrar las llaves con la nueva contraseña"
                        )
            except Exception as e:
                logger.warning(f"⚠️ Error probando nueva contraseña: {e}")
                # Intentar re-cifrar
                try:
                    success = keystore.reencrypt_keys(current_password, new_password)
                    if success:
                        logger.info("✅ Llaves re-cifradas correctamente con la nueva contraseña")
                    else:
                        logger.error("❌ No se pudieron re-cifrar las llaves")
                except Exception as reencrypt_error:
                    logger.error(f"❌ Error re-cifrando llaves: {reencrypt_error}")
                    # No bloqueamos el cambio, pero advertimos
    except Exception as e:
        logger.warning(f"⚠️ No se pudieron obtener llaves para re-cifrar: {e}")
    
    # 3. Guardar nuevo hash en BD
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
    
    # 4. Sincronizar contraseña de unseal (para el worker)
    try:
        # Verificar que la nueva contraseña funciona
        keys = keystore.get_keys(new_password)
        if keys:
            keystore.save_unseal_password(new_password)
            logger.info(f"✅ Contraseña de unseal actualizada. {len(keys)} llaves disponibles")
            
            # Actualizar worker
            from main import monitor_worker
            if monitor_worker:
                monitor_worker.set_password(new_password)
                logger.info("✅ Worker actualizado con nueva contraseña")
        else:
            logger.warning("⚠️ La nueva contraseña no puede descifrar llaves. El worker necesitará configuración manual.")
    except Exception as e:
        logger.error(f"❌ Error sincronizando contraseña de unseal: {e}")
        # No bloqueamos el cambio de contraseña
    
    logger.info("✅ Contraseña de admin actualizada correctamente")
    
    return {
        "message": "Contraseña actualizada correctamente",
        "success": True,
        "keys_available": keys_count > 0,
        "keys_decrypted": keys_decrypted
    }