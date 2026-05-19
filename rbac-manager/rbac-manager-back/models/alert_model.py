# backend/models/alert_model.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List 
from datetime import datetime

class CertificateAlertBase(BaseModel):
    user_id: Optional[int] = None
    days_before_expiration: int = Field(..., ge=1, le=365)
    is_active: bool = True
    notification_emails: Optional[str] = None  # 👈 Emails separados por comas

class CertificateAlertCreate(CertificateAlertBase):
    @field_validator('notification_emails')
    @classmethod
    def validate_emails(cls, v):
        if not v or not v.strip():
            raise ValueError('At least one notification email is required')
        
        # Validar formato de cada email
        emails = [email.strip() for email in v.split(',') if email.strip()]
        if not emails:
            raise ValueError('At least one notification email is required')
        
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        for email in emails:
            if not email_pattern.match(email):
                raise ValueError(f'Invalid email format: {email}')
        
        return v

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