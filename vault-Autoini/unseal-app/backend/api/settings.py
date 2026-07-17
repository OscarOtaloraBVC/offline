from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from core.database import AsyncSessionLocal
from core.crypto import SecureKeyStore
from api.auth import get_current_user
from worker.monitor_worker import MonitorWorker

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
            if request.threshold < 1:
                raise HTTPException(status_code=400, detail="Threshold debe ser al menos 1")
            keystore.set_threshold(request.threshold)
        
        # Actualizar namespace (persistir en base de datos)
        # Nota: Para simplicidad, se usa el método set_namespace directamente
        # En producción deberías guardar todas las configuraciones en la DB
        
        # Notificar al worker si es necesario
        if request.monitor_interval is not None:
            if request.monitor_interval < 10:
                raise HTTPException(status_code=400, detail="Intervalo mínimo 10 segundos")
            if request.monitor_interval > 300:
                raise HTTPException(status_code=400, detail="Intervalo máximo 300 segundos")
            
            # Actualizar interval en el worker
            from main import monitor_worker
            if monitor_worker:
                monitor_worker.monitor_interval = request.monitor_interval
        
        return {"message": "Configuración actualizada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando configuraciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))