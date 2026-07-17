# backend/api/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# ============================================
# CONFIGURACIÓN DESDE VARIABLES DE ENTORNO
# ============================================
# Todas las configuraciones vienen de Kubernetes (ConfigMap + Secret)

# Configuración JWT
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("❌ SECRET_KEY no está configurada en las variables de entorno")
logger.info(f"✅ SECRET_KEY configurada (longitud: {len(SECRET_KEY)})")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# Configuración de hash
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# Credenciales admin
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not ADMIN_PASSWORD:
    raise ValueError("❌ ADMIN_PASSWORD no está configurada en las variables de entorno")

# Truncar contraseña a 72 bytes para bcrypt (si se usa bcrypt)
# Con sha256_crypt no es necesario, pero mantenemos por seguridad
ADMIN_PASSWORD = ADMIN_PASSWORD[:72] if len(ADMIN_PASSWORD) > 72 else ADMIN_PASSWORD
ADMIN_PASSWORD_HASH = pwd_context.hash(ADMIN_PASSWORD)

logger.info(f"✅ Admin user '{ADMIN_USERNAME}' configurado correctamente")

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
# FUNCIONES DE AUTENTICACIÓN
# ============================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    # Truncar si es necesario (por si se usa bcrypt)
    plain_password = plain_password[:72] if len(plain_password) > 72 else plain_password
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error verificando contraseña: {e}")
        return False

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Crea un JWT token de acceso"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Obtiene el usuario actual desde el token JWT"""
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
# ENDPOINTS DE AUTENTICACIÓN
# ============================================

@router.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Autentica al usuario y retorna un token JWT"""
    # Verificar credenciales
    if login_data.username != ADMIN_USERNAME:
        logger.warning(f"Intento de login con usuario inválido: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Truncar contraseña por si acaso
    password = login_data.password[:72] if len(login_data.password) > 72 else login_data.password
    if not verify_password(password, ADMIN_PASSWORD_HASH):
        logger.warning(f"Intento de login con contraseña incorrecta para: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token
    access_token = create_access_token(data={"sub": login_data.username})
    
    logger.info(f"✅ Login exitoso para: {login_data.username}")
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/auth/verify")
async def verify_token(user: dict = Depends(get_current_user)):
    """Verifica si el token es válido"""
    return {"valid": True, "username": user["username"]}

@router.post("/auth/update-password")
async def update_password(
    request: PasswordUpdateRequest,
    user: dict = Depends(get_current_user)
):
    """Actualiza la contraseña del admin"""
    global ADMIN_PASSWORD_HASH
    
    # Truncar contraseñas por si acaso
    current_password = request.current_password[:72] if len(request.current_password) > 72 else request.current_password
    new_password = request.new_password[:72] if len(request.new_password) > 72 else request.new_password
    
    # Verificar contraseña actual
    if not verify_password(current_password, ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña actual incorrecta"
        )
    
    # Actualizar contraseña
    ADMIN_PASSWORD_HASH = pwd_context.hash(new_password)
    
    logger.info("✅ Contraseña de admin actualizada correctamente")
    
    # NOTA: En producción, deberías persistir esto en la base de datos
    # o actualizar el Secret en Kubernetes
    
    return {"message": "Contraseña actualizada correctamente"}