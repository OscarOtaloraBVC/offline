from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from core.database import AsyncSessionLocal
from core.crypto import SecureKeyStore
from api.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

class KeyCreateRequest(BaseModel):
    key: str = Field(..., min_length=44, max_length=44, description="Llave de unseal (44 caracteres)")
    password: str = Field(..., description="Contraseña del admin para descifrar/encifrar")

class KeyUpdateRequest(BaseModel):
    key: str = Field(..., min_length=44, max_length=44, description="Nueva llave de unseal")
    password: str = Field(..., description="Contraseña del admin")

class KeysResponse(BaseModel):
    keys: List[str]
    count: int
    threshold: int

def validate_key_format(key: str) -> bool:
    """Valida el formato de la llave de unseal (base64, 44 caracteres)"""
    import base64
    try:
        # Verificar que es base64 válido
        base64.b64decode(key)
        return len(key) == 44
    except:
        return False

@router.get("/keys", response_model=KeysResponse)
async def get_keys(user: dict = Depends(get_current_user)):
    """Obtiene las llaves de unseal (requiere autenticación)"""
    try:
        keystore = SecureKeyStore()
        
        # Obtener configuración
        settings = keystore.get_settings()
        threshold = settings.get("threshold", 2)
        
        # En producción, deberías solicitar la contraseña para descifrar
        # Por seguridad, no devolvemos las llaves en texto plano sin contraseña
        return {
            "keys": [],  # No devolvemos las llaves en claro sin autenticación adicional
            "count": 0,
            "threshold": threshold
        }
    except Exception as e:
        logger.error(f"Error obteniendo llaves: {e}")
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
        existing_keys = keystore.get_keys(request.password)
        
        if request.key in existing_keys:
            raise HTTPException(
                status_code=400,
                detail="La llave ya existe"
            )
        
        # Añadir nueva llave
        existing_keys.append(request.key)
        keystore.save_keys(existing_keys, request.password)
        
        return {"message": "Llave añadida correctamente", "total": len(existing_keys)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error añadiendo llave: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/keys/bulk")
async def add_keys_bulk(request: dict, user: dict = Depends(get_current_user)):
    """Añade múltiples llaves de unseal"""
    try:
        keys = request.get("keys", [])
        password = request.get("password", "")
        
        if not keys:
            raise HTTPException(status_code=400, detail="No se proporcionaron llaves")
        
        # Validar todas las llaves
        for key in keys:
            if not validate_key_format(key):
                raise HTTPException(
                    status_code=400,
                    detail=f"Formato inválido para llave: {key[:10]}..."
                )
        
        keystore = SecureKeyStore()
        keystore.save_keys(keys, password)
        
        return {"message": f"{len(keys)} llaves guardadas correctamente", "total": len(keys)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error añadiendo llaves bulk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/keys/{key_index}")
async def delete_key(key_index: int, request: dict, user: dict = Depends(get_current_user)):
    """Elimina una llave de unseal por índice"""
    try:
        password = request.get("password", "")
        
        keystore = SecureKeyStore()
        existing_keys = keystore.get_keys(password)
        
        if key_index < 1 or key_index > len(existing_keys):
            raise HTTPException(
                status_code=404,
                detail=f"Llave con índice {key_index} no encontrada"
            )
        
        # Eliminar la llave (índice 1-based)
        del existing_keys[key_index - 1]
        keystore.save_keys(existing_keys, password)
        
        return {"message": f"Llave {key_index} eliminada correctamente", "remaining": len(existing_keys)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando llave: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/keys/reorder")
async def reorder_keys(request: dict, user: dict = Depends(get_current_user)):
    """Reordena las llaves (cambia el orden de aplicación)"""
    try:
        order = request.get("order", [])
        password = request.get("password", "")
        
        keystore = SecureKeyStore()
        existing_keys = keystore.get_keys(password)
        
        if len(order) != len(existing_keys):
            raise HTTPException(
                status_code=400,
                detail=f"El orden debe tener {len(existing_keys)} elementos"
            )
        
        # Validar que el orden contiene todos los índices
        if sorted(order) != list(range(1, len(existing_keys) + 1)):
            raise HTTPException(
                status_code=400,
                detail="El orden debe ser una permutación de los índices existentes"
            )
        
        # Reordenar llaves
        reordered_keys = [existing_keys[i-1] for i in order]
        keystore.save_keys(reordered_keys, password)
        
        return {"message": "Orden actualizado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordenando llaves: {e}")
        raise HTTPException(status_code=500, detail=str(e))