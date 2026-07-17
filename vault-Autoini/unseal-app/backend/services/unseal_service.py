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
        
        # Primero verificar que el pod esté corriendo
        if not self.k8s.pod_is_running(pod_name):
            result["error"] = f"Pod {pod_name} no está corriendo"
            return result
        
        # Verificar estado actual
        try:
            status = await self.k8s.vault_status(pod_name, container_name)
        except Exception as e:
            result["error"] = f"Error obteniendo estado: {str(e)}"
            return result
        
        if not status.get("sealed", True):
            result["success"] = True
            result["details"].append("Pod ya está desbloqueado")
            return result
        
        # Aplicar llaves secuencialmente
        keys_to_use = keys[:threshold]
        logger.info(f"🔑 Aplicando {len(keys_to_use)} llaves a {pod_name}")
        
        for i, key in enumerate(keys_to_use, 1):
            try:
                logger.info(f"  🔑 Aplicando llave {i}/{len(keys_to_use)} a {pod_name}")
                
                unseal_result = await self.k8s.unseal_vault(pod_name, key, container_name)
                
                if unseal_result.get("success", False):
                    result["details"].append(f"Llave {i} aplicada correctamente")
                    result["keys_applied"] += 1
                    
                    # Verificar si ya está desbloqueado
                    await asyncio.sleep(1)
                    status = await self.k8s.vault_status(pod_name, container_name)
                    
                    if not status.get("sealed", True):
                        result["success"] = True
                        result["details"].append("✅ Pod desbloqueado exitosamente")
                        logger.info(f"✅ Pod {pod_name} desbloqueado con {i} llaves")
                        break
                else:
                    error_msg = unseal_result.get('error', 'Error desconocido')
                    result["details"].append(f"❌ Error aplicando llave {i}: {error_msg}")
                    result["error"] = error_msg
                    
                    # Si falla una llave, continuar con la siguiente
                    logger.warning(f"⚠️ Falló llave {i} para {pod_name}, probando siguiente...")
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Error en unseal de {pod_name}: {e}")
                result["error"] = str(e)
                # Continuar con la siguiente llave
                continue
        
        # Verificar estado final
        if not result["success"]:
            # Intentar verificar si al menos se desbloqueó parcialmente
            try:
                status = await self.k8s.vault_status(pod_name, container_name)
                if not status.get("sealed", True):
                    result["success"] = True
                    result["details"].append("✅ Pod fue desbloqueado en proceso")
            except:
                pass
        
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
            logger.error("❌ No se encontraron llaves de desbloqueo")
            return {"success": False, "error": "No hay llaves configuradas", "pods": []}
        
        # Obtener pods
        pods = self.k8s.get_vault_pods()
        
        if not pods:
            logger.info("ℹ️ No se encontraron pods de Vault")
            return {"success": True, "pods": [], "message": "No hay pods de Vault"}
        
        results = []
        
        for pod in pods:
            try:
                pod_name = pod.metadata.name
                logger.info(f"📦 Procesando {pod_name}")
                
                # Verificar que el pod está corriendo
                if not self.k8s.pod_is_running(pod_name):
                    logger.info(f"⚠️ Pod {pod_name} no está Running, intentando reiniciar...")
                    await self.k8s.restart_pod(pod_name)
                    # Esperar un tiempo limitado
                    await asyncio.sleep(30)
                    
                    # Si sigue sin correr, continuar con el siguiente
                    if not self.k8s.pod_is_running(pod_name):
                        logger.warning(f"⚠️ Pod {pod_name} no se recuperó, saltando")
                        results.append({
                            "pod": pod_name,
                            "success": False,
                            "error": "Pod no se recuperó después del reinicio"
                        })
                        continue
                
                # Desbloquear si es necesario
                unseal_result = await self.unseal_pod(pod_name, keys, threshold, container_name)
                results.append(unseal_result)
                
                # Pequeña pausa entre pods
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error procesando {pod_name}: {e}")
                results.append({
                    "pod": pod_name if 'pod_name' in locals() else "unknown",
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "pods": results,
            "total": len(results),
            "unsealed": sum(1 for r in results if r.get("success", False))
        }