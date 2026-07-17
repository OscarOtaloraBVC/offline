from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

router = APIRouter()
security = HTTPBearer()

# Configuración de autenticación
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

# Configurar hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Usuario admin desde variables de entorno
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = pwd_context.hash(os.getenv("ADMIN_PASSWORD", "admin123"))

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

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return pwd_context.verify(plain_password, hashed_password)

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
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Autentica al usuario y retorna un token JWT"""
    # Verificar credenciales
    if login_data.username != ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(login_data.password, ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token
    access_token = create_access_token(
        data={"sub": login_data.username}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/verify")
async def verify_token(user: dict = Depends(get_current_user)):
    """Verifica si el token es válido"""
    return {"valid": True, "username": user["username"]}

@router.post("/update-password")
async def update_password(
    request: PasswordUpdateRequest,
    user: dict = Depends(get_current_user)
):
    """Actualiza la contraseña del admin"""
    # Verificar contraseña actual
    if not verify_password(request.current_password, ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña actual incorrecta"
        )
    
    # Actualizar contraseña (en producción deberías persistirla)
    global ADMIN_PASSWORD_HASH
    ADMIN_PASSWORD_HASH = pwd_context.hash(request.new_password)
    
    # Aquí deberías guardar la nueva contraseña en un lugar seguro
    # Por simplicidad solo la actualizamos en memoria
    
    return {"message": "Contraseña actualizada correctamente"}