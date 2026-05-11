# backend/services/alert_service.py
import sqlite3
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

def check_expiring_certificates() -> List[CertificateExpiringInfo]:
    """
    Verificar certificados próximos a vencer y generar alertas.
    Esta función debe ejecutarse periódicamente (ej. cada hora via CronJob)
    """
    expiring_certs = []
    today = datetime.now()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Obtener usuarios con certificados y sus alertas configuradas
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
            LEFT JOIN certificate_alerts ca ON u.id = ca.user_id AND ca.is_active = 1
            WHERE u.state = 'ENABLED'
            GROUP BY u.id, ca.id
            ORDER BY u.id
        """)
        
        users_data = {}
        for row in cursor.fetchall():
            row_dict = dict(row)
            user_id = row_dict['user_id']
            
            if user_id not in users_data:
                # Calcular fecha de expiración
                cert_created = datetime.fromisoformat(row_dict['cert_created_at'])
                expiry_date = cert_created + timedelta(days=row_dict['cert_days'])
                days_until = (expiry_date - today).days
                
                users_data[user_id] = {
                    'user_id': user_id,
                    'username': row_dict['username'],
                    'expiry_date': expiry_date,
                    'days_until_expiry': days_until,
                    'alerts': []
                }
            
            if row_dict.get('alert_id'):
                users_data[user_id]['alerts'].append({
                    'id': row_dict['alert_id'],
                    'days_before': row_dict['days_before_expiration'],
                    'last_notified': row_dict['last_notified_at'],
                    'is_active': row_dict['alert_active']
                })
        
        # Verificar qué alertas deben dispararse
        for user_id, user_info in users_data.items():
            days_until = user_info['days_until_expiry']
            
            for alert in user_info['alerts']:
                # Si el certificado expira en menos o igual días que la alerta
                # Y no se ha notificado en las últimas 24 horas
                if days_until <= alert['days_before'] and days_until > 0:
                    should_notify = True
                    
                    if alert['last_notified']:
                        last_notified = datetime.fromisoformat(alert['last_notified'])
                        hours_since_notification = (today - last_notified).total_seconds() / 3600
                        # No notificar más de una vez cada 24 horas
                        if hours_since_notification < 24:
                            should_notify = False
                    
                    if should_notify:
                        # Marcar como notificado
                        _mark_alert_notified(alert['id'])
                        
                        # Añadir a la lista de expiración
                        expiring_certs.append(CertificateExpiringInfo(
                            user_id=user_info['user_id'],
                            username=user_info['username'],
                            days_until_expiry=days_until,
                            expiry_date=user_info['expiry_date'],
                            alerts_configured=[]  # Se puede cargar si es necesario
                        ))
    
    return expiring_certs

def _mark_alert_notified(alert_id: int):
    """Marcar una alerta como notificada"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE certificate_alerts 
            SET last_notified_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (alert_id,))
        conn.commit()