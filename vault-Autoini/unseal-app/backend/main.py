# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import logging
import os

from api import auth, keys, monitor, settings
from core.database import init_db
from worker.monitor_worker import MonitorWorker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Worker global
monitor_worker = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación"""
    global monitor_worker
    
    try:
        # Inicializar base de datos
        await init_db()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
    
    try:
        # Iniciar worker de monitoreo
        monitor_worker = MonitorWorker()
        
        # Configurar la contraseña desde variable de entorno
        vault_unseal_password = os.getenv("VAULT_UNSEAL_PASSWORD")
        if vault_unseal_password:
            monitor_worker.set_password(vault_unseal_password)
            logger.info("✅ Contraseña del worker configurada desde variable de entorno")
        else:
            logger.warning("⚠️ VAULT_UNSEAL_PASSWORD no configurada en variables de entorno")
        
        await monitor_worker.start()
        logger.info("✅ Worker de monitoreo iniciado")
    except Exception as e:
        logger.error(f"❌ Error iniciando worker: {e}")
    
    logger.info("🚀 Aplicación iniciada correctamente")
    
    yield
    
    # Limpieza al cerrar
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

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Incluir routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(keys.router, prefix="/api", tags=["keys"])
app.include_router(monitor.router, prefix="/api", tags=["monitor"])
app.include_router(settings.router, prefix="/api", tags=["settings"])

@app.get("/api/health")
async def health_check():
    """Endpoint de salud para verificaciones de Kubernetes"""
    return {
        "status": "healthy", 
        "worker_running": monitor_worker.is_running() if monitor_worker else False
    }

@app.get("/api/health/live")
async def liveness_check():
    """Liveness probe endpoint"""
    return {"status": "alive"}

@app.get("/api/health/ready")
async def readiness_check():
    """Readiness probe endpoint"""
    return {"status": "ready"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)