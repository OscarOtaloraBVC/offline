# backend/models/alert_model.py
from pydantic import BaseModel, Field
from typing import Optional, List  # 👈 'List'
from datetime import datetime

class CertificateAlertBase(BaseModel):
    user_id: int
    days_before_expiration: int = Field(..., ge=1, le=365)
    is_active: bool = True
    notification_emails: Optional[str] = None  # 👈 Emails separados por comas

class CertificateAlertCreate(CertificateAlertBase):
    pass

class CertificateAlertUpdate(BaseModel):
    days_before_expiration: Optional[int] = Field(None, ge=1, le=365)
    is_active: Optional[bool] = None
    notification_emails: Optional[str] = None # 👈 Emails

class CertificateAlert(CertificateAlertBase):
    id: int
    last_notified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CertificateExpiringInfo(BaseModel):
    user_id: int
    username: str
    days_until_expiry: int
    expiry_date: datetime
    alerts_configured: List[CertificateAlert]  # 👈