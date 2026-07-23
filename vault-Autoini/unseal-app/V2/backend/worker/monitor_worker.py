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
        
        # Intentar obtener la contraseña automáticamente
        if not self.password:
            await self.refresh_password()
        
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
    
    async def _ensure_pod_running(self, pod_name: str, container_name: str) -> bool:
        """
        Asegura que el pod esté Running, reiniciando si es necesario
        """
        # Verificar si el pod está corriendo
        if self.k8s_service.pod_is_running(pod_name):
            return True
        
        # Si no está Running, reiniciar
        logger.warning(f"⚠️ Pod {pod_name} no está Running. Intentando reiniciar...")
        
        success = await self.k8s_service.restart_pod(pod_name)
        if not success:
            logger.error(f"❌ No se pudo reiniciar {pod_name}")
            return False
        
        # Esperar a que el pod esté Running (máximo 30 segundos)
        ready = await self.k8s_service.wait_for_pod_running(pod_name, timeout=30, check_interval=2)
        
        if ready:
            logger.info(f"✅ Pod {pod_name} está Running")
            return True
        else:
            logger.error(f"❌ Pod {pod_name} no se recuperó después del reinicio")
            return False
    
    async def _monitor_loop(self):
        """Loop principal de monitoreo"""
        while self._running:
            try:
                # 🔄 OBTENER LA CONTRASEÑA DESDE LA BASE DE DATOS O CONFIGURACIÓN
                if not self.password:
                    logger.info("🔑 Intentando obtener la contraseña del sistema...")
                    
                    # Opción A: Desde variable de entorno (configuración de Kubernetes)
                    import os
                    env_password = os.getenv("VAULT_UNSEAL_PASSWORD")
                    if env_password:
                        logger.info("✅ Contraseña obtenida desde variable de entorno")
                        self.password = env_password
                    else:
                        # Opción B: Desde la base de datos (si está almacenada de forma segura)
                        try:
                            from core.database import AsyncSessionLocal
                            from sqlalchemy import select, text
                            
                            # NOTA: Esto es un ejemplo, NO almacenes contraseñas en texto plano
                            # Idealmente, deberías tener un mecanismo de recuperación de secrets
                            async with AsyncSessionLocal() as session:
                                # Si tienes una tabla de configuraciones con la contraseña
                                # Esto es solo un ejemplo, debes adaptarlo a tu estructura
                                result = await session.execute(
                                    text("SELECT value FROM system_config WHERE key = 'vault_password'")
                                )
                                row = result.fetchone()
                                if row:
                                    self.password = row[0]
                                    logger.info("✅ Contraseña obtenida desde la base de datos")
                        except Exception as e:
                            logger.warning(f"⚠️ No se pudo obtener contraseña de la BD: {e}")
                    
                    # Si aún no hay contraseña, esperar
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
                    # Si hay error al descifrar, podría ser que la contraseña cambió
                    # Intentar recargar la contraseña en el próximo ciclo
                    self.password = None
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
                
                logger.info(f"📊 Encontrados {len(pods)} pods de Vault")
                
                # Procesar cada pod
                for pod in pods:
                    try:
                        pod_name = pod.metadata.name
                        logger.info(f"📦 Procesando pod: {pod_name}")
                        
                        # === PASO 1: Asegurar que el pod esté Running ===
                        pod_ready = await self._ensure_pod_running(pod_name, container_name)
                        
                        if not pod_ready:
                            logger.warning(f"⚠️ Pod {pod_name} no está Running, saltando")
                            continue
                        
                        # === PASO 2: Verificar estado de Vault ===
                        try:
                            logger.info(f"🔍 Consultando estado de Vault en {pod_name}...")
                            status = await self.k8s_service.vault_status(pod_name, container_name)
                            
                            is_sealed = status.get("sealed", True)
                            error_msg = status.get("error")
                            
                            if error_msg and "exit code" not in error_msg.lower():
                                logger.warning(f"⚠️ Estado de {pod_name}: {error_msg}")
                            
                            if is_sealed:
                                logger.info(f"🔒 Pod {pod_name} está SELLADO. Iniciando desbloqueo...")
                                
                                # === PASO 3: Desbloquear el pod ===
                                threshold = settings.get("threshold", 2)
                                logger.info(f"🔑 Usando threshold={threshold}, llaves disponibles={len(keys)}")
                                
                                unseal_result = await self.unseal_service.unseal_pod(
                                    pod_name,
                                    keys,
                                    threshold,
                                    container_name
                                )
                                
                                if unseal_result.get("success", False):
                                    logger.info(f"✅ Pod {pod_name} DESBLOQUEADO exitosamente")
                                    logger.info(f"   Detalles: {unseal_result.get('details', [])}")
                                else:
                                    error_msg = unseal_result.get('error', 'Error desconocido')
                                    logger.error(f"❌ Error desbloqueando {pod_name}: {error_msg}")
                                    if unseal_result.get('details'):
                                        logger.warning(f"   Detalles: {unseal_result.get('details', [])}")
                            else:
                                logger.info(f"✅ Pod {pod_name} ya está desbloqueado")
                                
                        except Exception as e:
                            logger.error(f"❌ Error obteniendo estado de {pod_name}: {e}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error procesando pod {pod_name if 'pod_name' in locals() else 'unknown'}: {e}")
                        continue
                
                logger.info(f"✅ Ciclo completado. Próximo en {self.monitor_interval}s")
                await asyncio.sleep(self.monitor_interval)
                
            except asyncio.CancelledError:
                logger.info("Worker cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Error en worker: {e}")
                await asyncio.sleep(5)

    async def refresh_password(self):
        """Refresca la contraseña desde las fuentes disponibles"""
        import os
        
        # Intentar desde variable de entorno
        env_password = os.getenv("VAULT_UNSEAL_PASSWORD")
        if env_password:
            # Verificar que la contraseña funciona
            try:
                keys = self.keystore.get_keys(env_password)
                if keys:
                    self.password = env_password
                    logger.info(f"✅ Contraseña refrescada desde ENV. {len(keys)} llaves disponibles")
                    return True
            except Exception as e:
                logger.warning(f"⚠️ Contraseña de ENV no funciona: {e}")
        
        return False
    
    def is_running(self) -> bool:
        return self._running and self.task and not self.task.done()