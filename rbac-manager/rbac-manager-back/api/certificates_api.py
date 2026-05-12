# backend/api/certificates_api.py
from fastapi import APIRouter
from typing import List
from datetime import datetime, timedelta
from math import ceil
from database.db import get_db_connection
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix="/certificates",
    tags=["Certificates"]
)

class ExpiringCertificateInfo(BaseModel):
    user_id: int
    username: str
    days_until_expiry: int
    expiry_date: datetime
    certificate_created_at: datetime
    cert_days: int
    status: str  # 'critical', 'warning', 'healthy'

@router.get("/expiring", response_model=List[ExpiringCertificateInfo])
def get_expiring_certificates():
    """
    ENDPOINT PARA DASHBOARD - SOLO LECTURA
    Muestra todos los certificados que expiran en los próximos 30 días.
    NO depende de certificate_alerts.
    NO modifica la base de datos.
    """
    expiring_certs = []
    today = datetime.now()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Consulta simple - solo información básica, sin alerts
        cursor.execute("""
            SELECT 
                u.id as user_id,
                u.username,
                u.cert_days,
                uc.created_at as certificate_created_at
            FROM users u
            JOIN users_certs uc ON u.id = uc.user_id
            WHERE u.state = 'ENABLED'
            ORDER BY uc.created_at DESC
        """)
        
        for row in cursor.fetchall():
            row_dict = dict(row)
            cert_created = datetime.fromisoformat(row_dict['certificate_created_at'])
            expiry_date = cert_created + timedelta(days=row_dict['cert_days'])
            
            # Calcular días restantes (redondeando hacia arriba)
            #seconds_remaining = (expiry_date - today).total_seconds()
            #days_until = ceil(seconds_remaining / 86400) if seconds_remaining > 0 else 0
            #days_until = round(seconds_remaining / 86400) if seconds_remaining > 0 else 0
            days_until = (expiry_date.date() - today.date()).days
            if days_until < 0:
                days_until = 0
            
            # Determinar estado visual (solo para UI)
            if days_until <= 5:
                status = "critical"
            elif days_until <= 15:
                status = "warning"
            elif days_until <= 30:
                status = "attention"
            else:
                status = "healthy"
            
            # Solo incluir certificados que expiran en <= 30 días
            if days_until <= 30:
                expiring_certs.append(ExpiringCertificateInfo(
                    user_id=row_dict['user_id'],
                    username=row_dict['username'],
                    days_until_expiry=days_until,
                    expiry_date=expiry_date,
                    certificate_created_at=cert_created,
                    cert_days=row_dict['cert_days'],
                    status=status
                ))
    
    # Ordenar por días restantes (los más críticos primero)
    expiring_certs.sort(key=lambda x: x.days_until_expiry)
    return expiring_certs


@router.get("/all")
def get_all_certificates_status():
    """
    ENDPOINT PARA DEPURACIÓN
    Muestra TODOS los certificados con su estado
    """
    result = []
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
            ORDER BY u.id
        """)
        
        for row in cursor.fetchall():
            row_dict = dict(row)
            cert_created = datetime.fromisoformat(row_dict['certificate_created_at'])
            expiry_date = cert_created + timedelta(days=row_dict['cert_days'])
            seconds_remaining = (expiry_date - today).total_seconds()
            days_until = ceil(seconds_remaining / 86400) if seconds_remaining > 0 else 0
            
            result.append({
                "user_id": row_dict['user_id'],
                "username": row_dict['username'],
                "cert_days": row_dict['cert_days'],
                "certificate_created_at": row_dict['certificate_created_at'],
                "expiry_date": expiry_date.isoformat(),
                "days_until_expiry": days_until,
                "user_state": row_dict['state']
            })
    
    return result