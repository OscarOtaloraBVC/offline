from kubernetes import client, config
from kubernetes.stream import stream
import asyncio
import logging
import re

logger = logging.getLogger(__name__)

class KubernetesService:
    """Servicio para interactuar con Kubernetes API"""
    
    def __init__(self):
        try:
            # Cargar configuración desde dentro del cluster
            config.load_incluster_config()
        except:
            # Fallback para desarrollo local
            config.load_kube_config()
        
        self.core_v1 = client.CoreV1Api()
        self.namespace = "vault"  # Será configurable
    
    def set_namespace(self, namespace: str):
        self.namespace = namespace
    
    def get_vault_pods(self) -> list:
        """Obtiene todos los pods de Vault en el namespace"""
        try:
            pods = self.core_v1.list_namespaced_pod(self.namespace)
            vault_pods = [
                pod for pod in pods.items 
                if pod.metadata.name.startswith("vault-")
                and "vault-unseal" not in pod.metadata.name
            ]
            return vault_pods
        except Exception as e:
            logger.error(f"Error al obtener pods: {e}")
            return []
    
    def pod_is_running(self, pod_name: str) -> bool:
        """Verifica si un pod está en estado Running y Ready"""
        try:
            pod = self.core_v1.read_namespaced_pod(pod_name, self.namespace)
            
            if pod.status.phase != "Running":
                return False
            
            # Verificar que todos los contenedores están ready
            if pod.status.container_statuses:
                for container_status in pod.status.container_statuses:
                    if not container_status.ready:
                        return False
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error al verificar pod {pod_name}: {e}")
            return False
    
    async def exec_command(self, pod_name: str, container_name: str, command: list) -> tuple:
        """
        Ejecuta un comando en un contenedor de un pod usando la API de Kubernetes
        Retorna: (exit_code, stdout, stderr)
        """
        try:
            # Construir la llamada exec
            exec_command = command
            
            # Crear la solicitud de streaming
            resp = stream(
                self.core_v1.connect_get_namespaced_pod_exec,
                pod_name,
                self.namespace,
                container=container_name,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False
            )
            
            # Para comandos que no son interactivos, la respuesta es stdout o stderr
            # Pero necesitamos manejar ambos casos
            return 0, resp, ""
            
        except Exception as e:
            logger.error(f"Error ejecutando comando en {pod_name}: {e}")
            return 1, "", str(e)
    
    async def vault_status(self, pod_name: str, container_name: str = "vault") -> dict:
        """Obtiene el estado de Vault en un pod"""
        exit_code, stdout, stderr = await self.exec_command(
            pod_name,
            container_name,
            ["vault", "status"]
        )
        
        if exit_code != 0:
            return {"sealed": True, "error": stderr or stdout}
        
        # Parsear la salida para encontrar si está sealed
        sealed = "Sealed: true" in stdout
        return {"sealed": sealed, "output": stdout, "error": stderr}
    
    async def unseal_vault(self, pod_name: str, key: str, container_name: str = "vault") -> dict:
        """Ejecuta unseal en un pod de Vault"""
        exit_code, stdout, stderr = await self.exec_command(
            pod_name,
            container_name,
            ["vault", "operator", "unseal", key]
        )
        
        return {
            "success": exit_code == 0,
            "output": stdout,
            "error": stderr,
            "exit_code": exit_code
        }
    
    async def restart_pod(self, pod_name: str) -> bool:
        """Reinicia un pod eliminándolo (lo recreará el controller)"""
        try:
            self.core_v1.delete_namespaced_pod(pod_name, self.namespace)
            logger.info(f"Pod {pod_name} eliminado para reiniciar")
            return True
        except Exception as e:
            logger.error(f"Error al reiniciar pod {pod_name}: {e}")
            return False
    
    async def wait_for_pod_ready(self, pod_name: str, timeout: int = 150) -> bool:
        """Espera hasta que el pod esté Running y Ready"""
        import time
        
        for i in range(timeout // 5):  # 5 segundos de intervalo
            if self.pod_is_running(pod_name):
                return True
            
            logger.info(f"Esperando que {pod_name} esté ready... ({i*5}s)")
            await asyncio.sleep(5)
        
        logger.error(f"Timeout esperando que {pod_name} esté ready")
        return False