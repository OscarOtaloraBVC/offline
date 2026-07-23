# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from api import auth, keys, monitor, settings
from core.database import init_db
from core.crypto import SecureKeyStore
from worker.monitor_worker import MonitorWorker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

monitor_worker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación"""
    global monitor_worker
    
    # 1. Inicializar base de datos
    try:
        await init_db()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
    
    # 2. Inicializar SecureKeyStore
    try:
        keystore = SecureKeyStore()
        logger.info("✅ SecureKeyStore inicializado")
    except Exception as e:
        logger.error(f"❌ Error inicializando SecureKeyStore: {e}")
    
    # 3. Iniciar worker de monitoreo
    try:
        monitor_worker = MonitorWorker()
        
        keystore = SecureKeyStore()
        
        # Estrategia: Primero intentar con contraseña de unseal de la BD
        unseal_password = keystore.get_unseal_password()
        
        if unseal_password:
            try:
                keys = keystore.get_keys(unseal_password)
                if keys:
                    monitor_worker.set_password(unseal_password)
                    logger.info(f"✅ Worker cargado desde BD. {len(keys)} llaves disponibles")
                else:
                    logger.warning("⚠️ Contraseña de BD no descifra llaves, intentando ENV...")
                    env_password = os.getenv("VAULT_UNSEAL_PASSWORD")
                    if env_password:
                        try:
                            keys = keystore.get_keys(env_password)
                            if keys:
                                monitor_worker.set_password(env_password)
                                keystore.save_unseal_password(env_password)
                                logger.info(f"✅ Worker cargado desde ENV. {len(keys)} llaves disponibles")
                        except Exception as e:
                            logger.warning(f"⚠️ Contraseña ENV no funciona: {e}")
            except Exception as e:
                logger.warning(f"⚠️ Contraseña BD no funciona: {e}")
                env_password = os.getenv("VAULT_UNSEAL_PASSWORD")
                if env_password:
                    try:
                        keys = keystore.get_keys(env_password)
                        if keys:
                            monitor_worker.set_password(env_password)
                            keystore.save_unseal_password(env_password)
                            logger.info(f"✅ Worker cargado desde ENV. {len(keys)} llaves disponibles")
                    except Exception as e:
                        logger.warning(f"⚠️ Contraseña ENV no funciona: {e}")
        else:
            # No hay contraseña en BD, intentar con ENV
            env_password = os.getenv("VAULT_UNSEAL_PASSWORD")
            if env_password:
                try:
                    keys = keystore.get_keys(env_password)
                    if keys:
                        monitor_worker.set_password(env_password)
                        keystore.save_unseal_password(env_password)
                        logger.info(f"✅ Worker cargado desde ENV. {len(keys)} llaves disponibles")
                    else:
                        logger.warning("⚠️ Contraseña ENV no descifra llaves")
                except Exception as e:
                    logger.warning(f"⚠️ Contraseña ENV no funciona: {e}")
            else:
                logger.warning("⚠️ No hay contraseña de unseal configurada. El worker esperará configuración manual.")
        
        # Inyectar worker en el módulo monitor
        monitor.set_monitor_worker(monitor_worker)
        
        await monitor_worker.start()
        logger.info("✅ Worker de monitoreo iniciado")
    except Exception as e:
        logger.error(f"❌ Error iniciando worker: {e}")
    
    logger.info("🚀 Aplicación iniciada correctamente")
    
    yield
    
    # Limpieza
    try:
        if monitor_worker:
            await monitor_worker.stop()
            logger.info("✅ Worker de monitoreo detenido")
    except Exception as e:
        logger.error(f"❌ Error deteniendo worker: {e}")
    
    logger.info("👋 Aplicación cerrada correctamente")


app = FastAPI(
    title="Vault Unseal Manager",
    description="Sistema de auto-unseal para Vault con interfaz web",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(keys.router, prefix="/api", tags=["keys"])
app.include_router(monitor.router, prefix="/api", tags=["monitor"])
app.include_router(settings.router, prefix="/api", tags=["settings"])


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy", 
        "worker_running": monitor_worker.is_running() if monitor_worker else False
    }


@app.get("/api/health/live")
async def liveness_check():
    return {"status": "alive"}


@app.get("/api/health/ready")
async def readiness_check():
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)