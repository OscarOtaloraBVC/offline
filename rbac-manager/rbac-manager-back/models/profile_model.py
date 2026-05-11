# models/profile_model.py
from pydantic import BaseModel, Field
from typing import Optional

class ProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    type: str = Field(..., min_length=1, max_length=50)

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class Profile(ProfileBase):
    id: int

    class Config:
         from_attributes = True