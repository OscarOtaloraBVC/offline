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
        self._running = False  # Cambiado de is_running a _running
        self.task: Optional[asyncio.Task] = None
        self.keystore = SecureKeyStore()
        self.k8s_service = KubernetesService()
        self.unseal_service = UnsealService(self.k8s_service)
        self.password: Optional[str] = None
        self.monitor_interval = 30
    
    def set_password(self, password: str):
        """Establece la contraseña para descifrar llaves"""
        self.password = password
    
    async def start(self):
        """Inicia el worker de monitoreo"""
        if self._running:
            logger.warning("Worker ya está en ejecución")
            return
        
        self._running = True
        self.task = asyncio.create_task(self._monitor_loop())
        logger.info("Worker de monitoreo iniciado")
    
    async def stop(self):
        """Detiene el worker de monitoreo"""
        self._running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Worker de monitoreo detenido")
    
    async def _monitor_loop(self):
        """Loop principal de monitoreo"""
        while self._running:
            try:
                if self.password:
                    logger.info("Ejecutando ciclo de monitoreo...")
                    
                    # Obtener configuración
                    settings = self.keystore.get_settings()
                    namespace = settings.get("namespace", "vault")
                    container_name = settings.get("container_name", "vault")
                    self.monitor_interval = settings.get("monitor_interval", 30)
                    
                    # Ejecutar monitoreo y unseal
                    result = await self.unseal_service.monitor_and_unseal_all(
                        self.password,
                        namespace,
                        container_name
                    )
                    
                    if result.get("success", False):
                        logger.info(f"Ciclo completado: {result.get('unsealed', 0)}/{result.get('total', 0)} pods desbloqueados")
                    else:
                        logger.error(f"Error en ciclo de monitoreo: {result.get('error', 'Error desconocido')}")
                else:
                    logger.warning("Worker sin contraseña configurada")
                
                # Esperar intervalo
                await asyncio.sleep(self.monitor_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en worker de monitoreo: {e}")
                await asyncio.sleep(5)  # Esperar antes de reintentar
    
    def is_running(self) -> bool:
        """Verifica si el worker está en ejecución"""
        return self._running and self.task and not self.task.done()