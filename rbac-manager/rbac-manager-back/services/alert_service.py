# backend/services/alert_service.py
import sqlite3
from math import ceil
from typing import List, Optional
from datetime import datetime, timedelta
from database.db import get_db_connection
from models.alert_model import CertificateAlert, CertificateAlertCreate, CertificateExpiringInfo
import logging

logger = logging.getLogger(__name__)


def create_alert(alert_in: CertificateAlertCreate) -> Optional[CertificateAlert]:
    """Crear una nueva alerta de certificado"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO certificate_alerts (user_id, days_before_expiration, is_active)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, days_before_expiration) DO UPDATE SET
                    is_active = excluded.is_active,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, user_id, days_before_expiration, is_active, 
                          last_notified_at, created_at, updated_at
            """, (alert_in.user_id, alert_in.days_before_expiration, alert_in.is_active))
            
            row = cursor.fetchone()
            conn.commit()
            
            if row:
                return CertificateAlert(**dict(row))
    except sqlite3.Error as e:
        logger.error(f"Error creating alert: {e}")
    return None


def get_user_alerts(user_id: int) -> List[CertificateAlert]:
    """Obtener todas las alertas de un usuario"""
    alerts = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, days_before_expiration, is_active,
                   last_notified_at, created_at, updated_at
            FROM certificate_alerts
            WHERE user_id = ?
            ORDER BY days_before_expiration
        """, (user_id,))
        
        for row in cursor.fetchall():
            alerts.append(CertificateAlert(**dict(row)))
    return alerts


def delete_alert(alert_id: int) -> bool:
    """Eliminar una alerta"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM certificate_alerts WHERE id = ?", (alert_id,))
        conn.commit()
        return cursor.rowcount > 0


def check_and_send_alerts() -> List[dict]:
    """
    🔔 SISTEMA DE ALERTAS - SOLO PARA NOTIFICACIONES
    - Usa certificate_alerts
    - Usa last_notified_at (cooldown 24h)
    - NO debe ser usado por el dashboard
    """
    notifications_sent = []
    today = datetime.now()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Obtener usuarios con certificados Y alertas configuradas
        cursor.execute("""
            SELECT 
                u.id as user_id,
                u.username,
                u.cert_days,
                uc.created_at as cert_created_at,
                ca.id as alert_id,
                ca.days_before_expiration,
                ca.last_notified_at,
                ca.is_active as alert_active
            FROM users u
            JOIN users_certs uc ON u.id = uc.user_id
            JOIN certificate_alerts ca ON u.id = ca.user_id AND ca.is_active = 1
            WHERE u.state = 'ENABLED'
            ORDER BY u.id
        """)
        
        for row in cursor.fetchall():
            row_dict = dict(row)
            
            # Calcular días restantes
            cert_created = datetime.fromisoformat(row_dict['cert_created_at'])
            expiry_date = cert_created + timedelta(days=row_dict['cert_days'])
            seconds_remaining = (expiry_date - today).total_seconds()
            days_until = ceil(seconds_remaining / 86400) if seconds_remaining > 0 else 0
            
            # Verificar si debemos notificar
            if days_until <= row_dict['days_before_expiration'] and days_until >= 0:
                should_notify = True
                
                # Cooldown: no notificar más de una vez cada 24 horas
                if row_dict['last_notified_at']:
                    last_notified = datetime.fromisoformat(row_dict['last_notified_at'])
                    hours_since = (today - last_notified).total_seconds() / 3600
                    if hours_since < 24:
                        should_notify = False
                        print(f"⏸️ Cooldown: {row_dict['username']} - Last notified {hours_since:.1f}h ago")
                
                if should_notify:
                    # Marcar como notificada
                    cursor.execute("""
                        UPDATE certificate_alerts 
                        SET last_notified_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (row_dict['alert_id'],))
                    conn.commit()
                    
                    # Aquí iría el envío real (email, webhook, etc.)
                    notification = {
                        "user_id": row_dict['user_id'],
                        "username": row_dict['username'],
                        "days_until_expiry": days_until,
                        "expiry_date": expiry_date.isoformat(),
                        "alert_days_before": row_dict['days_before_expiration'],
                        "sent_at": datetime.now().isoformat()
                    }
                    notifications_sent.append(notification)
                    
                    # TODO: Enviar email/slack/webhook
                    print(f"📧 ALERT: {notification}")
    
    return notifications_sent