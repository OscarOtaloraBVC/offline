from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class SettingsBase(BaseModel):
    """Modelo base para configuraciones"""
    threshold: Optional[int] = Field(2, ge=1, le=10, description="Número de llaves requeridas")
    namespace: Optional[str] = Field("vault", min_length=1, description="Namespace de Kubernetes")
    container_name: Optional[str] = Field("vault", min_length=1, description="Nombre del contenedor de Vault")
    monitor_interval: Optional[int] = Field(30, ge=10, le=300, description="Intervalo de monitoreo en segundos")

class SettingsCreate(SettingsBase):
    """Modelo para crear configuraciones"""
    password: str = Field(..., min_length=4, description="Contraseña del admin")

class SettingsUpdate(SettingsBase):
    """Modelo para actualizar configuraciones"""
    password: Optional[str] = Field(None, description="Contraseña del admin (requerida si se cambia threshold)")

class SettingsResponse(SettingsBase):
    """Respuesta con configuraciones"""
    id: int = Field(1, description="ID de la configuración (siempre 1)")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class SettingsOperationResponse(BaseModel):
    """Respuesta para operaciones con configuraciones"""
    success: bool
    message: str
    settings: Optional[SettingsResponse] = None
    error: Optional[str] = None

class SystemStatusResponse(BaseModel):
    """Estado del sistema"""
    version: str = "1.0.0"
    worker_running: bool
    keys_configured: int
    threshold: int
    namespace: str
    monitor_interval: int
    last_check: Optional[datetime] = None
    uptime: Optional[int] = None  # segundos