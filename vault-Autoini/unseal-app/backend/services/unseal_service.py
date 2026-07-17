import logging
import asyncio
from typing import List, Dict
from services.k8s_service import KubernetesService
from core.database import AsyncSessionLocal
from core.crypto import SecureKeyStore

logger = logging.getLogger(__name__)

class UnsealService:
    """Servicio que maneja la lógica de desbloqueo de Vault"""
    
    def __init__(self, k8s_service: KubernetesService):
        self.k8s = k8s_service
        self.keystore = SecureKeyStore()
    
    async def get_unseal_keys(self, password: str) -> List[str]:
        """Obtiene las llaves de desbloqueo desde el almacén seguro"""
        try:
            return self.keystore.get_keys(password)
        except Exception as e:
            logger.error(f"Error obteniendo llaves de desbloqueo: {e}")
            return []
    
    async def get_threshold(self) -> int:
        """Obtiene el threshold configurado"""
        return self.keystore.get_threshold()
    
    async def unseal_pod(self, pod_name: str, keys: List[str], threshold: int, container_name: str = "vault") -> Dict:
        """
        Intenta desbloquear un pod usando las llaves proporcionadas
        """
        result = {
            "pod": pod_name,
            "success": False,
            "keys_applied": 0,
            "details": [],
            "error": None
        }
        
        # Primero verificar estado actual
        status = await self.k8s.vault_status(pod_name, container_name)
        
        if not status.get("sealed", True):
            result["success"] = True
            result["details"].append("Pod ya está desbloqueado")
            return result
        
        # Aplicar llaves secuencialmente
        keys_to_use = keys[:threshold]
        
        for i, key in enumerate(keys_to_use):
            try:
                logger.info(f"Aplicando llave {i+1}/{threshold} a {pod_name}")
                
                unseal_result = await self.k8s.unseal_vault(pod_name, key, container_name)
                
                if unseal_result["success"]:
                    result["details"].append(f"Llave {i+1} aplicada correctamente")
                    result["keys_applied"] += 1
                    
                    # Verificar si ya está desbloqueado
                    await asyncio.sleep(2)
                    status = await self.k8s.vault_status(pod_name, container_name)
                    
                    if not status.get("sealed", True):
                        result["success"] = True
                        result["details"].append("Pod desbloqueado exitosamente")
                        break
                else:
                    result["details"].append(f"Error aplicando llave {i+1}: {unseal_result['error']}")
                    result["error"] = unseal_result['error']
                    
                    # Si falla una llave, interrumpir el proceso
                    break
                    
            except Exception as e:
                logger.error(f"Error en unseal de {pod_name}: {e}")
                result["error"] = str(e)
                break
        
        return result
    
    async def monitor_and_unseal_all(self, password: str, namespace: str, container_name: str = "vault") -> Dict:
        """
        Monitorea todos los pods de Vault y los desbloquea si es necesario
        """
        self.k8s.set_namespace(namespace)
        settings = self.keystore.get_settings()
        threshold = settings.get("threshold", 2)
        
        # Obtener llaves
        keys = await self.get_unseal_keys(password)
        
        if not keys:
            logger.error("No se encontraron llaves de desbloqueo")
            return {"success": False, "error": "No hay llaves configuradas", "pods": []}
        
        # Obtener pods
        pods = self.k8s.get_vault_pods()
        
        if not pods:
            logger.info("No se encontraron pods de Vault")
            return {"success": True, "pods": [], "message": "No hay pods de Vault"}
        
        results = []
        
        for pod in pods:
            pod_name = pod.metadata.name
            logger.info(f"Procesando {pod_name}")
            
            # Verificar que el pod está corriendo
            if not self.k8s.pod_is_running(pod_name):
                logger.info(f"Pod {pod_name} no está Running, reiniciando...")
                await self.k8s.restart_pod(pod_name)
                await self.k8s.wait_for_pod_ready(pod_name)
            
            # Desbloquear si es necesario
            unseal_result = await self.unseal_pod(pod_name, keys, threshold, container_name)
            results.append(unseal_result)
        
        return {
            "success": True,
            "pods": results,
            "total": len(results),
            "unsealed": sum(1 for r in results if r["success"])
        }