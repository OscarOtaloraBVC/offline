# models/user_model.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from .profile_model import Profile

class UserAssignmentCreate(BaseModel):
    profile_id: int
    namespace: Optional[str] = None

class UserAssignment(BaseModel):
    profile: Profile
    namespace: Optional[str]

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    cert_days: int = Field(..., ge=0)
    observations: Optional[str] = None
    state: str = None

class UserCreate(UserBase):
    assignments: Optional[List[UserAssignmentCreate]] = None

class UserUpdate(UserBase):
    model_config = ConfigDict(extra='ignore')
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    cert_days: Optional[int] = Field(None, ge=0)
    observations: Optional[str] = None 
    state: Optional[str] = None # Opcional en actualizaciones
    assignments: Optional[List[UserAssignmentCreate]] = None

class User(UserBase):
    id: int
    updated_at: datetime 
    assignments: List[UserAssignment] = []
    profiles: List[Profile] = [] 
    namespaces: List[dict] = []

    class Config:
         from_attributes = True
