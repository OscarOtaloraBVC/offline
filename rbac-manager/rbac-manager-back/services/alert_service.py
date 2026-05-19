# backend/services/alert_service.py
import sqlite3
from math import ceil
from typing import List, Optional
from datetime import datetime, timedelta
from database.db import get_db_connection
from models.alert_model import CertificateAlert, CertificateAlertCreate, CertificateExpiringInfo
from services.email_service import send_certificate_alert_email
from services.email_service import send_certificate_report_email
import logging

logger = logging.getLogger(__name__)


def create_alert(alert_in: CertificateAlertCreate) -> Optional[CertificateAlert]:
    """Crear una nueva alerta de certificado"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO certificate_alerts (user_id, days_before_expiration, is_active, notification_emails)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, days_before_expiration) DO UPDATE SET
                    is_active = excluded.is_active,
                    notification_emails = excluded.notification_emails,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, user_id, days_before_expiration, is_active, 
                        last_notified_at, created_at, updated_at, notification_emails
            """, (alert_in.user_id, alert_in.days_before_expiration, alert_in.is_active, alert_in.notification_emails))
            
            row = cursor.fetchone()
            conn.commit()
            
            if row:
                return CertificateAlert(**dict(row))
            return None
    except sqlite3.Error as e:
        logger.error(f"Error creating alert: {e}")
        print(f"❌ SQLite error: {e}")
    return None


def get_user_alerts(user_id: int) -> List[CertificateAlert]:
    """Obtener todas las alertas de un usuario"""
    alerts = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, days_before_expiration, is_active,
                last_notified_at, created_at, updated_at, notification_emails
            FROM certificate_alerts
            WHERE user_id = ?
            ORDER BY days_before_expiration
        """, (user_id,))
        
        for row in cursor.fetchall():
            alerts.append(CertificateAlert(**dict(row)))
    return alerts

def get_global_alert() -> Optional[CertificateAlert]:
    """Obtiene la alerta global configurada (user_id IS NULL)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, days_before_expiration, is_active,
                last_notified_at, created_at, updated_at, notification_emails
            FROM certificate_alerts
            WHERE user_id IS NULL AND is_active = 1
            ORDER BY id DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return CertificateAlert(**dict(row))
    return None

def delete_alert(alert_id: int) -> bool:
    """Eliminar una alerta"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM certificate_alerts WHERE id = ?", (alert_id,))
        conn.commit()
        return cursor.rowcount > 0
    
def delete_global_alert() -> bool:
    """Elimina completamente la alerta global"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM certificate_alerts WHERE user_id IS NULL")
        conn.commit()
        return cursor.rowcount > 0

def check_and_send_alerts() -> dict:
    """
    Envía un ÚNICO reporte con TODOS los certificados próximos a expirar.
    Retorna un diccionario con el resultado del envío.
    """
    # 1. Obtener la alerta global configurada
    global_alert = get_global_alert()
    
    if not global_alert:
        return {
            "success": False,
            "message": "No active global alert configured",
            "report_sent": False
        }
    
    # 2. Verificar cooldown (no enviar más de una vez cada X horas)
    today = datetime.now()
    if global_alert.last_notified_at is not None:
        last_notified = datetime.fromisoformat(global_alert.last_notified_at)
        hours_since = (today - last_notified).total_seconds() / 3600
        if hours_since < 24:  # Cooldown de 24 horas    👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈👈 
            return {
                "success": False,
                "message": f"Report already sent {hours_since:.1f} hours ago. Cooldown active.",
                "report_sent": False,
                "last_sent": global_alert.last_notified_at.isoformat()
            }
    
    # 3. Obtener todos los certificados próximos a expirar (próximos 30 días)
    expiring_certs = get_all_expiring_certificates(days_threshold=30)
    
    if not expiring_certs:
        return {
            "success": True,
            "message": "No expiring certificates found. No report sent.",
            "report_sent": False,
            "certificates_count": 0
        }
    
    # 4. Parsear destinatarios de email
    emails_str = global_alert.notification_emails or ''
    emails = [e.strip() for e in emails_str.split(',') if e.strip()]
    
    if not emails:
        return {
            "success": False,
            "message": "No email recipients configured in global alert",
            "report_sent": False
        }
    
    # 5. Enviar el reporte único
    email_sent = send_certificate_report_email(
        to_emails=emails,
        expiring_certificates=expiring_certs,
        days_threshold=global_alert.days_before_expiration
    )
    
    # 6. Actualizar last_notified_at
    if email_sent:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE certificate_alerts 
                SET last_notified_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (global_alert.id,))
            conn.commit()
    
    return {
        "success": email_sent,
        "report_sent": email_sent,
        "certificates_count": len(expiring_certs),
        "emails_sent_to": emails if email_sent else [],
        "sent_at": datetime.now().isoformat(),
        "message": "Report sent successfully" if email_sent else "Failed to send report"
    }

def get_all_expiring_certificates(days_threshold: int = 30) -> List[dict]:
    """
    Obtiene TODOS los certificados que expiran en los próximos 'days_threshold' días.
    Retorna una lista enriquecida para el reporte.
    """
    expiring_certs = []
    today = datetime.now()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                u.id as user_id,
                u.username,
                u.cert_days,
                uc.created_at as certificate_created_at,
                u.state
            FROM users u
            JOIN users_certs uc ON u.id = uc.user_id
            WHERE u.state = 'ENABLED'
            ORDER BY uc.created_at DESC
        """)
        
        for row in cursor.fetchall():
            row_dict = dict(row)
            cert_created = datetime.fromisoformat(row_dict['certificate_created_at'])
            expiry_date = cert_created + timedelta(days=row_dict['cert_days'])
            days_until = (expiry_date.date() - today.date()).days
            
            if 0 < days_until <= days_threshold:
                # Determinar nivel de urgencia
                if days_until <= 5:
                    status = "critical"
                    status_text = "CRÍTICO"
                elif days_until <= 15:
                    status = "warning"
                    status_text = "ADVERTENCIA"
                else:
                    status = "attention"
                    status_text = "ATENCIÓN"
                
                expiring_certs.append({
                    "user_id": row_dict['user_id'],
                    "username": row_dict['username'],
                    "days_until_expiry": days_until,
                    "expiry_date": expiry_date,
                    "expiry_date_str": expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "cert_days": row_dict['cert_days'],
                    "status": status,
                    "status_text": status_text,
                    "created_at": cert_created
                })
    
    # Ordenar por días restantes (los más críticos primero)
    expiring_certs.sort(key=lambda x: x['days_until_expiry'])
    return expiring_certs

def save_global_alert(alert_in: CertificateAlertCreate) -> Optional[CertificateAlert]:
    """
    Guarda o actualiza la alerta global (user_id = None).
    Solo puede existir una alerta global activa.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Primero, desactivar cualquier otra alerta global existente
            cursor.execute("""
                UPDATE certificate_alerts 
                SET is_active = 0 
                WHERE user_id IS NULL
            """)
            
            # Crear la nueva alerta global
            cursor.execute("""
                INSERT INTO certificate_alerts (user_id, days_before_expiration, is_active, notification_emails)
                VALUES (NULL, ?, ?, ?)
                RETURNING id, user_id, days_before_expiration, is_active, 
                        last_notified_at, created_at, updated_at, notification_emails
            """, (alert_in.days_before_expiration, alert_in.is_active, alert_in.notification_emails))
            
            row = cursor.fetchone()
            conn.commit()
            
            if row:
                return CertificateAlert(**dict(row))
            return None
    except sqlite3.Error as e:
        logger.error(f"Error saving global alert: {e}")
        return None

def get_global_alert_config() -> Optional[CertificateAlert]:
    """Obtiene la configuración actual de la alerta global"""
    return get_global_alert()

def send_manual_alert_notification(alert_id: int) -> Optional[dict]:
    """
    Envía una notificación manual para una alerta específica
    (se puede enviar en cualquier momento)
    """
    from services.user_service import get_user
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Obtener la alerta con información del usuario
        cursor.execute("""
            SELECT 
                ca.id, ca.user_id, ca.days_before_expiration, ca.notification_emails,
                u.username, u.cert_days, u.state,
                uc.created_at as cert_created_at
            FROM certificate_alerts ca
            JOIN users u ON ca.user_id = u.id
            JOIN users_certs uc ON u.id = uc.user_id
            WHERE ca.id = ? AND ca.is_active = 1 AND u.state = 'ENABLED'
            ORDER BY uc.id DESC
            LIMIT 1
        """, (alert_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        row_dict = dict(row)
        
        # Calcular días restantes
        from datetime import datetime, timedelta
        from math import ceil
        
        today = datetime.now()
        cert_created = datetime.fromisoformat(row_dict['cert_created_at'])
        expiry_date = cert_created + timedelta(days=row_dict['cert_days'])
        seconds_remaining = (expiry_date - today).total_seconds()
        days_until = ceil(seconds_remaining / 86400) if seconds_remaining > 0 else 0
        
        # Parsear emails
        emails_str = row_dict.get('notification_emails', '')
        emails = [e.strip() for e in emails_str.split(',') if e.strip()] if emails_str else []
        
        # Enviar email si hay destinatarios
        email_sent = False
        if emails:
            email_sent = send_certificate_alert_email(
                to_emails=emails,
                username=row_dict['username'],
                days_until=days_until,
                expiry_date=expiry_date.strftime("%Y-%m-%d %H:%M:%S")
            )
        
        # Actualizar last_notified_at (igual para manual o automático)
        cursor.execute("""
            UPDATE certificate_alerts 
            SET last_notified_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (alert_id,))
        conn.commit()
        
        return {
            "success": True,
            "alert_id": alert_id,
            "user_id": row_dict['user_id'],
            "username": row_dict['username'],
            "days_until_expiry": days_until,
            "expiry_date": expiry_date.isoformat(),
            "emails_sent_to": emails if email_sent else [],
            "email_sent": email_sent,
            "notified_at": datetime.now().isoformat()
        }