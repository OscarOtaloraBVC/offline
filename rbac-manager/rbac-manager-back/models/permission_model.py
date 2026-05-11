# models/permission_model.py
from pydantic import BaseModel, Field
from typing import Optional

class PermissionBase(BaseModel):
    resource: str = Field(..., min_length=1, max_length=255, description="The API resource this permission applies to (e.g., '/pods', '/deployments')")
    resource_api: Optional[str] = Field(None, description="The API group/version")
    resource_namespaced: bool = Field(default=True, description="Whether the resource is namespaced (True) or cluster-wide (False)")
    is_verb_get: bool = Field(default=False, description="Permission to GET a single resource.")
    is_verb_list: bool = Field(default=False, description="Permission to LIST collections of resources.")
    is_verb_watch: bool = Field(default=False, description="Permission to WATCH for changes to resources.")
    is_verb_create: bool = Field(default=False, description="Permission to CREATE new resources.")
    is_verb_update: bool = Field(default=False, description="Permission to UPDATE existing resources (full update).")
    is_verb_patch: bool = Field(default=False, description="Permission to PATCH existing resources (partial update).")
    is_verb_delete: bool = Field(default=False, description="Permission to DELETE a single resource.")
    is_verb_deletecollection: bool = Field(default=False, description="Permission to DELETE a collection of resources.")

class PermissionCreate(PermissionBase):
    # profile_id will typically be provided by the path parameter
    # e.g., POST /profiles/{profile_id}/permissions
    # If you need to include it in the body, add:
    # profile_id: int
    pass

class PermissionUpdate(BaseModel): # Separate update model for flexibility
    resource: Optional[str] = Field(None, min_length=1, max_length=255)
    resource_api: Optional[str] = None
    resource_namespaced: Optional[bool] = None
    is_verb_get: Optional[bool] = None
    is_verb_list: Optional[bool] = None
    is_verb_watch: Optional[bool] = None
    is_verb_create: Optional[bool] = None
    is_verb_update: Optional[bool] = None
    is_verb_patch: Optional[bool] = None
    is_verb_delete: Optional[bool] = None
    is_verb_deletecollection: Optional[bool] = None

class Permission(PermissionBase):
    id: int
    profile_id: int # Since it's NOT NULL in the DB, it should be present here

    class Config:
        from_attributes = True # Pydantic V2 (for V1, use orm_mode = True)
        # Example for Pydantic V1 users:
        # orm_mode = True