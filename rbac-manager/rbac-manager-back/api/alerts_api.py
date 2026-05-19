# backend/api/alerts_api.py - MODIFICADO
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from models.alert_model import CertificateAlert, CertificateAlertCreate, CertificateExpiringInfo
from services.email_service import test_smtp_connection
from database.db import get_db_connection
import services.alert_service as alert_service
import services.user_service as user_service

router = APIRouter(
    prefix="/alerts",
    tags=["Certificate Alerts"]
)

@router.get("/global", response_model=Optional[CertificateAlert])
def get_global_alert():
    """Obtiene la configuración de alerta global (reporte consolidado)"""
    return alert_service.get_global_alert_config()

@router.post("/global", response_model=CertificateAlert, status_code=status.HTTP_201_CREATED)
def create_or_update_global_alert(alert_in: CertificateAlertCreate):
    """
    Crea o actualiza la alerta global (user_id = None)
    """
    # Validar que haya al menos un email
    if not alert_in.notification_emails or not alert_in.notification_emails.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one notification email is required"
        )
    
    # Validar formato de emails
    emails = [e.strip() for e in alert_in.notification_emails.split(',') if e.strip()]
    if not emails:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one notification email is required"
        )
    
    import re
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    invalid_emails = [e for e in emails if not email_pattern.match(e)]
    
    if invalid_emails:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email format: {', '.join(invalid_emails)}"
        )
    
    # Asegurar que user_id sea None
    alert_in.user_id = None
    alert = alert_service.save_global_alert(alert_in)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not save global alert configuration"
        )
    return alert

@router.delete("/global", status_code=status.HTTP_204_NO_CONTENT)
def delete_global_alert():
    """Elimina la configuración de alerta global"""
    from database.db import get_db_connection
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM certificate_alerts WHERE user_id IS NULL")
        conn.commit()
        deleted = cursor.rowcount > 0
        
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No global alert configuration found to delete"
        )
    return None

@router.post("/send-notifications")
def send_notifications():
    """
    Ejecuta la verificación de certificados y envía un reporte consolidado.
    Debe ser llamado por un CronJob.
    """
    result = alert_service.check_and_send_alerts()
    return result

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