from kubernetes import client, config
from kubernetes.stream import stream
import asyncio
import logging
import re
import subprocess

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
        self.namespace = "vault"
    
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
        Ejecuta un comando en un contenedor de un pod usando kubectl
        Retorna: (exit_code, stdout, stderr)
        """
        try:
            # Construir el comando kubectl
            cmd = [
                "kubectl", "exec", pod_name,
                "-n", self.namespace,
                "-c", container_name,
                "--"
            ] + command
            
            logger.debug(f"Ejecutando: {' '.join(cmd)}")
            
            # Ejecutar el comando
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Limpiar la salida
            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""
            
            return result.returncode, stdout, stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ejecutando comando en {pod_name}")
            return 1, "", "Timeout"
        except Exception as e:
            logger.error(f"Error ejecutando comando en {pod_name}: {e}")
            return 1, "", str(e)
    
    async def vault_status(self, pod_name: str, container_name: str = "vault") -> dict:
        """
        Obtiene el estado de Vault en un pod
        Retorna un dict con:
            - sealed: bool (True si está sellado)
            - output: str (salida del comando)
            - error: str (mensaje de error si existe)
        """
        try:
            logger.info(f"Consultando estado de Vault en pod: {pod_name}")
            
            exit_code, stdout, stderr = await self.exec_command(
                pod_name,
                container_name,
                ["vault", "status"]
            )
            
            # Log para debug
            logger.info(f"Pod {pod_name}: exit_code={exit_code}, stdout_len={len(stdout)}, stderr_len={len(stderr)}")
            
            # Si el comando falló porque el container no existe, retornar error
            if "container not found" in stderr or "container not found" in stdout:
                logger.error(f"Container '{container_name}' no encontrado en pod {pod_name}")
                return {
                    "sealed": True,
                    "output": stdout,
                    "error": f"Contenedor '{container_name}' no encontrado"
                }
            
            # Si el pod no está corriendo
            if not self.pod_is_running(pod_name):
                logger.warning(f"Pod {pod_name} no está corriendo")
                return {
                    "sealed": True,
                    "output": stdout,
                    "error": "Pod no está en estado Running"
                }
            
            # Analizar la salida completa para determinar el estado
            combined_output = stdout + "\n" + stderr
            
            # Buscar la línea "Sealed: true/false"
            sealed_match = re.search(r'Sealed:\s*(true|false)', combined_output, re.IGNORECASE)
            
            if sealed_match:
                sealed_value = sealed_match.group(1).lower()
                is_sealed = sealed_value == "true"
                logger.info(f"Pod {pod_name}: Sealed={is_sealed} (detectado en salida)")
                return {
                    "sealed": is_sealed,
                    "output": stdout,
                    "error": stderr if stderr else None
                }
            
            # Si no se encontró "Sealed:", intentar determinar por exit_code
            if exit_code == 0:
                # Si exit_code es 0, normalmente está desbloqueado
                logger.info(f"Pod {pod_name}: exit_code=0, asumiendo desbloqueado")
                return {
                    "sealed": False,
                    "output": stdout,
                    "error": stderr if stderr else None
                }
            else:
                # Si exit_code != 0, está sellado o hay error
                logger.info(f"Pod {pod_name}: exit_code={exit_code}, asumiendo sellado")
                return {
                    "sealed": True,
                    "output": stdout,
                    "error": stderr if stderr else f"Exit code: {exit_code}"
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estado de Vault para {pod_name}: {e}")
            return {
                "sealed": True,
                "error": str(e)
            }
    
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