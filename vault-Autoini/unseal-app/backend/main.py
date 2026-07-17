from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import logging

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
    
    # Inicializar base de datos
    await init_db()
    
    # Iniciar worker de monitoreo
    monitor_worker = MonitorWorker()
    await monitor_worker.start()
    
    logger.info("Aplicación iniciada correctamente")
    
    yield
    
    # Limpieza al cerrar
    if monitor_worker:
        await monitor_worker.stop()
    logger.info("Aplicación cerrada correctamente")

app = FastAPI(
    title="Vault Unseal Manager",
    description="Sistema de auto-unseal para Vault con interfaz web",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Incluir routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(keys.router, prefix="/api/keys", tags=["keys"])
app.include_router(monitor.router, prefix="/api/monitor", tags=["monitor"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])

@app.get("/api/health")
async def health_check():
    """Endpoint de salud para verificaciones de Kubernetes"""
    return {"status": "healthy", "worker_running": monitor_worker.is_running() if monitor_worker else False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)