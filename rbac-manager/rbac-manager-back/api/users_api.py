# api/users_api.py
from fastapi import APIRouter, HTTPException, status
from typing import List
from models.user_model import User, UserCreate, UserUpdate
import services.user_service as user_service

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_new_user(user_in: UserCreate):
    # Basic validation for profile_ids (ensure they exist)
    # This could be moved to the service layer for better separation
    # For now, let's assume profile_ids are valid or the DB will catch it
    user = user_service.create_user(user_in)
    if not user:
        # This could be due to username conflict or invalid profile_id
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User could not be created. Username might exist or invalid profile ID provided.")
    return user

@router.get("/", response_model=List[User])
def read_users():
    return user_service.list_users()

@router.get("/{user_id}", response_model=User)
def read_user(user_id: int):
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/{user_id}", response_model=User)
def update_existing_user(user_id: int, user_in: UserUpdate):
    # Similar to create, could add profile_id validation here or in service
    user = user_service.update_user(user_id, user_in)
    if not user:
        existing = user_service.get_user(user_id)
        if not existing:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        else: # Likely username conflict or invalid profile ID during update
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User could not be updated. Username might conflict, invalid profile ID, or no changes made.")
    return user

@router.put("/disable/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def disable_user(user_id: int, user_in: UserUpdate):
    user_service.disable_user(user_id)
    return None
    

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(user_id: int):
    deleted = user_service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None
