# backend/api/alerts_api.py - MODIFICADO
from fastapi import APIRouter, HTTPException, status
from typing import List
from models.alert_model import CertificateAlert, CertificateAlertCreate, CertificateExpiringInfo
from services.email_service import test_smtp_connection
import services.alert_service as alert_service
import services.user_service as user_service

router = APIRouter(
    prefix="/alerts",
    tags=["Certificate Alerts"]
)

# CRUD de alertas (mantiene igual)
@router.post("/", response_model=CertificateAlert, status_code=status.HTTP_201_CREATED)
def create_certificate_alert(alert_in: CertificateAlertCreate):
    """Crear una alerta para un usuario"""
    user = user_service.get_user(alert_in.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    alert = alert_service.create_alert(alert_in)
    if not alert:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create alert")
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

# 🔔 NUEVO: Endpoint para que el CronJob ejecute las alertas
@router.post("/send-notifications")
def send_notifications():
    """
    Ejecuta la verificación de alertas y envía notificaciones.
    Debe ser llamado por un CronJob
    """
    notifications = alert_service.check_and_send_alerts()
    return {
        "success": True,
        "notifications_sent": len(notifications),
        "details": notifications
    }

@router.get("/test-email")
def test_email_config():
    """Prueba la configuración SMTP"""
    result = test_smtp_connection()
    return result

@router.post("/test-send")
def test_send_email(to_email: str):
    """Envía un email de prueba"""
    from services.email_service import send_certificate_alert_email
    
    success = send_certificate_alert_email(
        to_emails=[to_email],
        username="test_user",
        days_until=15,
        expiry_date="2024-12-31 23:59:59"
    )
    return {"success": success, "message": "Email sent" if success else "Failed to send"}

@router.post("/{alert_id}/notify-now")
def send_manual_notification(alert_id: int):
    """
    Envía una notificación manual para una alerta específica
    Actualiza last_notified_at
    """
    from services.alert_service import send_manual_alert_notification
    
    result = send_manual_alert_notification(alert_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Alert not found or user has no valid certificate"
        )
    return result