# api/profiles_api.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models.profile_model import Profile, ProfileCreate, ProfileUpdate
from models.permission_model import PermissionCreate
import services.profile_service as profile_service
import os
import json

router = APIRouter(
    prefix="/profiles",
    tags=["Profiles"]
)

@router.post("/", response_model=Profile, status_code=status.HTTP_201_CREATED)
def create_new_profile(profile_in: ProfileCreate):
    profile = profile_service.create_profile(profile_in)
    if not profile:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile with this name already exists or invalid data.")
    return profile

@router.get("/", response_model=List[Profile])
def read_profiles():
    return profile_service.list_profiles()

@router.get("/additional-resources")
def get_additional_resources():
    default_resources = [
        { "namespaced": True, "resource": "pods/exec", "apiversion": "v1" },
        { "namespaced": True, "resource": "pods/portforward", "apiversion": "v1" },
        { "namespaced": True, "resource": "pods/log", "apiversion": "v1" },
        { "namespaced": True, "resource": "pods/proxy", "apiversion": "v1" }
    ]
    resources = os.getenv("RBAC_ADDITIONAL_RESOURCES")
    if not resources:
        return default_resources
    try:
        return json.loads(resources)
    except json.JSONDecodeError:
        return default_resources

@router.get("/{profile_id}", response_model=Profile)
def read_profile(profile_id: int):
    profile = profile_service.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile

@router.put("/{profile_id}", response_model=Profile)
def update_existing_profile(profile_id: int, profile_in: ProfileUpdate):
    profile = profile_service.update_profile(profile_id, profile_in)
    if not profile:
        # Could be not found or name conflict
        existing = profile_service.get_profile(profile_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile name conflict or no changes made.")
    return profile

@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_profile(profile_id: int):
    deleted = profile_service.delete_profile(profile_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return None # FastAPI handles 204 No Content correctly


@router.post("/save-permissions", status_code=status.HTTP_201_CREATED)
def create_new_user_list(profile_id: int, permissions_list: List[PermissionCreate]):
    success = profile_service.save_profile_permissions(profile_id,permissions_list)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more user namespaces could not be created."
        )
    return {"success": True, "message": "Namespaces created successfully"}

@router.get("/{profile_id}/permissions")
def read_permissions_for_profile(profile_id: int):
    """
    Retrieve all permissions associated with a specific profile ID.
    """
    profile = profile_service.get_profile(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with id {profile_id} not found"
        )

    permissions_list = profile_service.get_permissions_list(profile_id=profile_id)
    return permissions_list