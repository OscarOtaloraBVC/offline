# worker/monitor_worker.py
import asyncio
import logging
from typing import Optional
import time

from core.database import AsyncSessionLocal
from core.crypto import SecureKeyStore
from services.k8s_service import KubernetesService
from services.unseal_service import UnsealService

logger = logging.getLogger(__name__)

class MonitorWorker:
    """Worker asíncrono que ejecuta el monitoreo continuo de Vault"""
    
    def __init__(self):
        self._running = False
        self.task: Optional[asyncio.Task] = None
        self.keystore = SecureKeyStore()
        self.k8s_service = KubernetesService()
        self.unseal_service = UnsealService(self.k8s_service)
        self.password: Optional[str] = None
        self.monitor_interval = 30
        self._last_check_time = None
    
    def set_password(self, password: str):
        """Establece la contraseña para descifrar llaves"""
        self.password = password
        logger.info("🔑 Contraseña del worker configurada")
    
    async def start(self):
        """Inicia el worker de monitoreo"""
        if self._running:
            logger.warning("⚠️ Worker ya está en ejecución")
            return
        
        self._running = True
        self.task = asyncio.create_task(self._monitor_loop())
        logger.info("🚀 Worker de monitoreo iniciado")
    
    async def stop(self):
        """Detiene el worker de monitoreo"""
        self._running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Worker de monitoreo detenido")
    
    async def _monitor_loop(self):
        """Loop principal de monitoreo"""
        while self._running:
            try:
                if not self.password:
                    logger.warning("⚠️ Worker sin contraseña configurada")
                    await asyncio.sleep(10)
                    continue
                
                # Obtener configuración
                settings = self.keystore.get_settings()
                namespace = settings.get("namespace", "vault")
                container_name = settings.get("container_name", "vault")
                self.monitor_interval = settings.get("monitor_interval", 30)
                
                # Verificar si hay llaves configuradas
                try:
                    keys = self.keystore.get_keys(self.password)
                    if not keys:
                        logger.warning("⚠️ No hay llaves configuradas")
                        await asyncio.sleep(self.monitor_interval)
                        continue
                    logger.info(f"🔑 {len(keys)} llaves cargadas correctamente")
                except Exception as e:
                    logger.error(f"❌ Error obteniendo llaves: {e}")
                    await asyncio.sleep(self.monitor_interval)
                    continue
                
                logger.info("🔄 Ejecutando ciclo de monitoreo...")
                
                # Configurar el namespace
                self.k8s_service.set_namespace(namespace)
                
                # Obtener todos los pods de Vault
                pods = self.k8s_service.get_vault_pods()
                
                if not pods:
                    logger.info("ℹ️ No se encontraron pods de Vault")
                    await asyncio.sleep(self.monitor_interval)
                    continue
                
                # Procesar cada pod
                for pod in pods:
                    try:
                        pod_name = pod.metadata.name
                        logger.info(f"📦 Procesando pod: {pod_name}")
                        
                        # Verificar si el pod está corriendo
                        is_running = self.k8s_service.pod_is_running(pod_name)
                        
                        if not is_running:
                            logger.warning(f"⚠️ Pod {pod_name} no está corriendo")
                            
                            # Intentar reiniciar el pod
                            try:
                                logger.info(f"🔄 Intentando reiniciar {pod_name}...")
                                success = await self.k8s_service.restart_pod(pod_name)
                                if success:
                                    logger.info(f"✅ Pod {pod_name} reiniciado. Esperando 20s...")
                                    await asyncio.sleep(20)
                                    
                                    # Verificar si está corriendo
                                    is_running = self.k8s_service.pod_is_running(pod_name)
                                    if is_running:
                                        logger.info(f"✅ Pod {pod_name} se recuperó")
                                    else:
                                        logger.warning(f"⚠️ Pod {pod_name} no se recuperó, saltando")
                                        continue
                                else:
                                    logger.error(f"❌ No se pudo reiniciar {pod_name}")
                                    continue
                            except Exception as e:
                                logger.error(f"❌ Error reiniciando {pod_name}: {e}")
                                continue
                        
                        # Si el pod NO está corriendo, saltar
                        if not is_running:
                            continue
                        
                        # Si el pod está corriendo, verificar estado de Vault
                        try:
                            status = await self.k8s_service.vault_status(pod_name, container_name)
                            is_sealed = status.get("sealed", True)
                            
                            if is_sealed:
                                logger.info(f"🔒 Pod {pod_name} está SELLADO. Intentando desbloquear...")
                                
                                # Intentar desbloquear
                                unseal_result = await self.unseal_service.unseal_pod(
                                    pod_name,
                                    keys,
                                    settings.get("threshold", 2),
                                    container_name
                                )
                                
                                if unseal_result.get("success", False):
                                    logger.info(f"✅ Pod {pod_name} DESBLOQUEADO exitosamente")
                                else:
                                    error_msg = unseal_result.get('error', 'Error desconocido')
                                    logger.error(f"❌ Error desbloqueando {pod_name}: {error_msg}")
                            else:
                                logger.info(f"✅ Pod {pod_name} ya está desbloqueado")
                                
                        except Exception as e:
                            logger.error(f"❌ Error obteniendo estado de {pod_name}: {e}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error procesando pod: {e}")
                        continue
                
                logger.info(f"✅ Ciclo completado. Próximo en {self.monitor_interval}s")
                await asyncio.sleep(self.monitor_interval)
                
            except asyncio.CancelledError:
                logger.info("Worker cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Error en worker: {e}")
                await asyncio.sleep(5)
    
    def is_running(self) -> bool:
        return self._running and self.task and not self.task.done()