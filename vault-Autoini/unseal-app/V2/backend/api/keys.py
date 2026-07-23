from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import base64
import sqlite3

from core.crypto import SecureKeyStore
from api.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class KeyCreateRequest(BaseModel):
    key: str = Field(..., min_length=44, max_length=44, description="Llave de unseal (44 caracteres)")
    password: str = Field(..., description="Contraseña del admin para cifrar")


class KeysResponse(BaseModel):
    keys: List[str]
    count: int
    threshold: int


class DeleteKeyRequest(BaseModel):
    password: str


def validate_key_format(key: str) -> bool:
    """Valida el formato de la llave de unseal (base64, 44 caracteres)"""
    try:
        base64.b64decode(key)
        return len(key) == 44
    except:
        return False


@router.get("/keys", response_model=KeysResponse)
async def get_keys(
    password: Optional[str] = Query(None, description="Contraseña del admin para descifrar las llaves"),
    user: dict = Depends(get_current_user)
):
    """
    Obtiene las llaves de unseal (requiere autenticación)
    Si se proporciona password, devuelve las llaves descifradas
    Si no, devuelve solo el count y threshold
    """
    try:
        keystore = SecureKeyStore()
        
        # Obtener configuración
        settings = keystore.get_settings()
        threshold = settings.get("threshold", 2)
        
        # Si no se proporciona contraseña, solo devolver metadata
        if not password:
            count = keystore.get_key_count()
            
            return KeysResponse(
                keys=[],
                count=count,
                threshold=threshold
            )
        
        # Si se proporciona contraseña, descifrar y devolver las llaves
        try:
            keys = keystore.get_keys(password)
            logger.info(f"✅ Obtenidas {len(keys)} llaves para usuario {user['username']}")
            
            return KeysResponse(
                keys=keys,
                count=len(keys),
                threshold=threshold
            )
        except Exception as e:
            logger.error(f"❌ Error descifrando llaves: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña incorrecta o no se pudieron descifrar las llaves"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo llaves: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keys")
async def add_key(request: KeyCreateRequest, user: dict = Depends(get_current_user)):
    """Añade una nueva llave de unseal"""
    try:
        # Validar formato
        if not validate_key_format(request.key):
            raise HTTPException(
                status_code=400,
                detail="Formato de llave inválido. Debe ser base64 de 44 caracteres"
            )
        
        keystore = SecureKeyStore()
        
        # Obtener llaves existentes
        try:
            existing_keys = keystore.get_keys(request.password)
        except Exception as e:
            logger.error(f"Error obteniendo llaves existentes: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña incorrecta o no se pudieron descifrar las llaves"
            )
        
        if request.key in existing_keys:
            raise HTTPException(
                status_code=400,
                detail="La llave ya existe"
            )
        
        # Añadir nueva llave
        existing_keys.append(request.key)
        keystore.save_keys(existing_keys, request.password)
        
        logger.info(f"✅ Usuario {user['username']} añadió una llave. Total: {len(existing_keys)}")
        
        return {
            "message": "Llave añadida correctamente",
            "total": len(existing_keys),
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error añadiendo llave: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/keys/{key_index}")
async def delete_key(
    key_index: int, 
    request: DeleteKeyRequest, 
    user: dict = Depends(get_current_user)
):
    """Elimina una llave de unseal por índice"""
    try:
        password = request.password
        
        keystore = SecureKeyStore()
        existing_keys = keystore.get_keys(password)
        
        if key_index < 1 or key_index > len(existing_keys):
            raise HTTPException(
                status_code=404,
                detail=f"Llave con índice {key_index} no encontrada"
            )
        
        deleted_key = existing_keys.pop(key_index - 1)
        keystore.save_keys(existing_keys, password)
        
        logger.info(f"✅ Usuario {user['username']} eliminó la llave {key_index}")
        
        return {
            "message": f"Llave {key_index} eliminada correctamente",
            "remaining": len(existing_keys),
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error eliminando llave: {e}")
        raise HTTPException(status_code=500, detail=str(e))