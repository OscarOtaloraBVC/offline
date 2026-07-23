from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
import logging

from core.crypto import SecureKeyStore
from api.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class SettingsUpdateRequest(BaseModel):
    threshold: Optional[int] = None
    namespace: Optional[str] = None
    container_name: Optional[str] = None
    monitor_interval: Optional[int] = None
    password: Optional[str] = None


class SettingsResponse(BaseModel):
    threshold: int
    namespace: str
    container_name: str
    monitor_interval: int


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(user: dict = Depends(get_current_user)):
    """Obtiene la configuración actual"""
    try:
        keystore = SecureKeyStore()
        settings = keystore.get_settings()
        
        return SettingsResponse(
            threshold=settings.get("threshold", 2),
            namespace=settings.get("namespace", "vault"),
            container_name=settings.get("container_name", "vault"),
            monitor_interval=settings.get("monitor_interval", 30)
        )
    except Exception as e:
        logger.error(f"Error obteniendo configuraciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_settings(request: SettingsUpdateRequest, user: dict = Depends(get_current_user)):
    """Actualiza la configuración"""
    try:
        keystore = SecureKeyStore()
        
        # Validar threshold
        if request.threshold is not None:
            if request.threshold < 1 or request.threshold > 10:
                raise HTTPException(status_code=400, detail="Threshold debe estar entre 1 y 10")
            keystore.set_threshold(request.threshold)
        
        # Obtener configuraciones actuales
        current_settings = keystore.get_settings()
        
        # Actualizar con nuevos valores
        updated_settings = {
            "threshold": request.threshold or current_settings.get("threshold", 2),
            "namespace": request.namespace or current_settings.get("namespace", "vault"),
            "container_name": request.container_name or current_settings.get("container_name", "vault"),
            "monitor_interval": request.monitor_interval or current_settings.get("monitor_interval", 30)
        }
        
        # Validar intervalo
        if request.monitor_interval is not None:
            if request.monitor_interval < 10:
                raise HTTPException(status_code=400, detail="Intervalo mínimo 10 segundos")
            if request.monitor_interval > 300:
                raise HTTPException(status_code=400, detail="Intervalo máximo 300 segundos")
            updated_settings["monitor_interval"] = request.monitor_interval
        
        # Guardar configuraciones
        keystore.save_settings(updated_settings)
        
        # Actualizar interval en el worker
        if request.monitor_interval is not None:
            from main import monitor_worker
            if monitor_worker:
                monitor_worker.monitor_interval = request.monitor_interval
                logger.info(f"✅ Intervalo de monitoreo actualizado a {request.monitor_interval}s")
        
        logger.info(f"✅ Configuraciones actualizadas por {user['username']}")
        return {"message": "Configuración actualizada correctamente", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando configuraciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))