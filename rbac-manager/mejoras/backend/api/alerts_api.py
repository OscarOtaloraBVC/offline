# backend/api/alerts_api.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models.alert_model import CertificateAlert, CertificateAlertCreate, CertificateExpiringInfo
import services.alert_service as alert_service
import services.user_service as user_service

router = APIRouter(
    prefix="/alerts",
    tags=["Certificate Alerts"]
)

@router.post("/", response_model=CertificateAlert, status_code=status.HTTP_201_CREATED)
def create_certificate_alert(alert_in: CertificateAlertCreate):
    """Crear una alerta para un usuario"""
    # Verificar que el usuario existe
    user = user_service.get_user(alert_in.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    alert = alert_service.create_alert(alert_in)
    if not alert:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                          detail="Could not create alert")
    return alert

@router.get("/user/{user_id}", response_model=List[CertificateAlert])
def get_user_alerts(user_id: int):
    """Obtener todas las alertas de un usuario"""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return alert_service.get_user_alerts(user_id)

@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(alert_id: int):
    """Eliminar una alerta"""
    deleted = alert_service.delete_alert(alert_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return None

@router.get("/check-expiring", response_model=List[CertificateExpiringInfo])
def check_expiring_certificates():
    """
    Endpoint para verificar certificados próximos a vencer.
    Debe ser llamado por un CronJob periódicamente.
    """
    return alert_service.check_expiring_certificates()