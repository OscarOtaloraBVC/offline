from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import asyncio
import os

from api.auth import get_current_user
from services.k8s_service import KubernetesService
from services.unseal_service import UnsealService
from core.crypto import SecureKeyStore
from worker.monitor_worker import MonitorWorker

router = APIRouter()
logger = logging.getLogger(__name__)


class MonitorStatusResponse(BaseModel):
    running: bool
    last_check: Optional[str] = None
    pods_status: List[Dict]
    total_pods: int
    sealed_pods: int
    unsealed_pods: int


class TriggerUnsealRequest(BaseModel):
    password: str
    namespace: Optional[str] = None
    container_name: Optional[str] = None


class TriggerUnsealResponse(BaseModel):
    success: bool
    pods_processed: int
    pods_unsealed: int
    details: List[Dict]
    error: Optional[str] = None


class SetPasswordRequest(BaseModel):
    password: str


# Instancia global del worker (se inyecta desde main)
monitor_worker_instance: Optional[MonitorWorker] = None


def set_monitor_worker(worker: MonitorWorker):
    """Inyecta la instancia del worker"""
    global monitor_worker_instance
    monitor_worker_instance = worker


@router.get("/monitor/status", response_model=MonitorStatusResponse)
async def get_monitor_status(user: dict = Depends(get_current_user)):
    """Obtiene el estado actual del monitoreo"""
    try:
        keystore = SecureKeyStore()
        settings = keystore.get_settings()
        namespace = settings.get("namespace", "vault")
        container_name = settings.get("container_name", "vault")
        
        k8s = KubernetesService()
        k8s.set_namespace(namespace)
        
        pods = k8s.get_vault_pods()
        pods_status = []
        sealed = 0
        unsealed = 0
        
        for pod in pods:
            pod_name = pod.metadata.name
            is_running = k8s.pod_is_running(pod_name)
            
            # Intentar obtener estado de Vault
            vault_status = {"sealed": True, "error": "No disponible"}
            if is_running:
                try:
                    status = await k8s.vault_status(pod_name, container_name)
                    vault_status = status
                except Exception as e:
                    logger.error(f"Error obteniendo estado de {pod_name}: {e}")
                    vault_status = {"sealed": True, "error": str(e)}
            
            is_sealed = vault_status.get("sealed", True)
            pod_phase = pod.status.phase if pod.status else "Unknown"
            error_msg = vault_status.get("error")
            
            if not is_running:
                error_msg = error_msg or "Pod no está corriendo"
            
            if is_sealed:
                sealed += 1
            else:
                unsealed += 1
            
            pods_status.append({
                "name": pod_name,
                "running": is_running,
                "sealed": is_sealed,
                "status": pod_phase,
                "vault_status": vault_status.get("output", ""),
                "error": error_msg
            })
        
        return MonitorStatusResponse(
            running=monitor_worker_instance.is_running() if monitor_worker_instance else False,
            last_check=None,
            pods_status=pods_status,
            total_pods=len(pods_status),
            sealed_pods=sealed,
            unsealed_pods=unsealed
        )
    except Exception as e:
        logger.error(f"Error obteniendo estado del monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/trigger", response_model=TriggerUnsealResponse)
async def trigger_unseal(
    request: TriggerUnsealRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Ejecuta un ciclo de desbloqueo manual"""
    try:
        keystore = SecureKeyStore()
        settings = keystore.get_settings()
        
        namespace = request.namespace or settings.get("namespace", "vault")
        container_name = request.container_name or settings.get("container_name", "vault")
        
        k8s = KubernetesService()
        unseal_service = UnsealService(k8s)
        
        # Ejecutar el unseal
        result = await unseal_service.monitor_and_unseal_all(
            request.password,
            namespace,
            container_name
        )
        
        if not result.get("success", False):
            return TriggerUnsealResponse(
                success=False,
                pods_processed=0,
                pods_unsealed=0,
                details=[],
                error=result.get("error", "Error desconocido")
            )
        
        pods = result.get("pods", [])
        unsealed_count = sum(1 for p in pods if p.get("success", False))
        
        return TriggerUnsealResponse(
            success=True,
            pods_processed=len(pods),
            pods_unsealed=unsealed_count,
            details=pods,
            error=None
        )
    except Exception as e:
        logger.error(f"Error en trigger de unseal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/restart")
async def restart_monitor(user: dict = Depends(get_current_user)):
    """Reinicia el worker de monitoreo"""
    global monitor_worker_instance
    
    if not monitor_worker_instance:
        raise HTTPException(status_code=404, detail="Worker no inicializado")
    
    try:
        await monitor_worker_instance.stop()
        await monitor_worker_instance.start()
        return {"message": "Worker reiniciado correctamente"}
    except Exception as e:
        logger.error(f"Error reiniciando worker: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitor/sync-password")
async def sync_worker_password(user: dict = Depends(get_current_user)):
    """
    Sincroniza la contraseña del worker con la contraseña del admin actual.
    Útil cuando se cambió la contraseña del admin y se quiere actualizar el worker.
    """
    try:
        # Obtener la contraseña del admin actual desde la BD
        # Nota: No tenemos la contraseña en texto plano, solo el hash
        # Por lo tanto, este endpoint requiere que el usuario proporcione la contraseña
        raise HTTPException(
            status_code=400,
            detail="Este endpoint requiere la contraseña actual. Usa /monitor/set-password"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sincronizando contraseña: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/set-password")
async def set_worker_password(
    request: SetPasswordRequest,
    user: dict = Depends(get_current_user)
):
    """Configura la contraseña del worker para descifrar llaves"""
    global monitor_worker_instance
    
    password = request.password
    if not password:
        raise HTTPException(status_code=400, detail="Contraseña requerida")
    
    if not monitor_worker_instance:
        raise HTTPException(status_code=404, detail="Worker no inicializado")
    
    try:
        keystore = SecureKeyStore()
        keys = keystore.get_keys(password)
        
        if not keys:
            raise HTTPException(
                status_code=400, 
                detail="No se pudieron descifrar las llaves con la contraseña proporcionada"
            )
        
        # Guardar la contraseña en la BD para que persista
        keystore.save_unseal_password(password)
        
        # Actualizar el worker
        monitor_worker_instance.set_password(password)
        
        logger.info(f"✅ Contraseña del worker configurada por {user['username']}. {len(keys)} llaves disponibles")
        
        return {
            "message": "Contraseña configurada correctamente", 
            "keys_count": len(keys),
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configurando contraseña: {e}")
        raise HTTPException(status_code=500, detail=str(e))