# models/user_profile_namespace_association_model.py
from pydantic import BaseModel

class UserProfileNamespaceAssociationBase(BaseModel):
    user_id: int
    profile_id: int
    namespace: str

class UserProfileNamespaceAssociationCreate(UserProfileNamespaceAssociationBase):
    pass

class UserProfileNamespaceAssociation(UserProfileNamespaceAssociationBase):
    class Config:
        from_attributes = True