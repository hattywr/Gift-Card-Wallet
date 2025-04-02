# users.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import date, datetime

from ..database import get_db
from ..models import User
from ..security import get_current_user, get_password_hash, verify_password
from ..logger import setup_logger

# Initialize logger
logger = setup_logger(__name__, "main.log")

router = APIRouter(prefix="/users", tags=["users"])

class UserProfileResponse(BaseModel):
    user_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    date_of_birth: date
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[constr(min_length=1, max_length=50)] = None
    last_name: Optional[constr(min_length=1, max_length=50)] = None
    date_of_birth: Optional[date] = None

    class Config:
        from_attributes = True

class PasswordUpdateRequest(BaseModel):
    current_password: str
    new_password: constr(min_length=8)
    
    class Config:
        from_attributes = True

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get the profile of the currently authenticated user"""
    logger.info(f"User {current_user.username} requested their profile")
    return current_user

@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a user profile by ID (only accessible by the same user)"""
    logger.info(f"User {current_user.username} requested profile for user ID: {user_id}")
    
    # Verify permissions
    if current_user.user_id != user_id:
        logger.warning(f"Unauthorized attempt to access user profile: User {current_user.user_id} tried to access user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user profile"
        )
    
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            logger.warning(f"User not found with ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"Successfully retrieved profile for user {user.username}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user profile for {user_id}: {str(e)}", exc_info=True)
        raise

@router.put("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the profile of the currently authenticated user"""
    logger.info(f"User {current_user.username} is updating their profile")
    
    try:
        # Update user fields if provided
        if update_data.email is not None:
            current_user.email = update_data.email
        
        if update_data.first_name is not None:
            current_user.first_name = update_data.first_name
        
        if update_data.last_name is not None:
            current_user.last_name = update_data.last_name
        
        if update_data.date_of_birth is not None:
            current_user.date_of_birth = update_data.date_of_birth
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Successfully updated profile for user {current_user.username}")
        return current_user
    except IntegrityError:
        db.rollback()
        logger.error(f"Integrity error updating user {current_user.username} - likely duplicate email", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use by another account"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating profile for user {current_user.username}: {str(e)}", exc_info=True)
        raise

@router.put("/me/password")
async def update_password(
    password_data: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the password of the currently authenticated user"""
    logger.info(f"User {current_user.username} is attempting to change password")
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        logger.warning(f"Failed password change attempt for user {current_user.username}: incorrect current password")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Verify new password meets complexity requirements
    if not any(c.isupper() for c in password_data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="New password must contain at least one uppercase letter"
        )
    if not any(c.islower() for c in password_data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="New password must contain at least one lowercase letter"
        )
    if not any(c.isdigit() for c in password_data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="New password must contain at least one number"
        )
    
    try:
        # Hash and update the new password
        current_user.password_hash = get_password_hash(password_data.new_password)
        db.commit()
        
        logger.info(f"Password successfully changed for user {current_user.username}")
        return {"message": "Password updated successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating password for user {current_user.username}: {str(e)}", exc_info=True)
        raise

@router.delete("/me")
async def delete_account(
    current_password: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete the currently authenticated user's account"""
    logger.info(f"User {current_user.username} is attempting to delete their account")
    
    # Verify current password
    if not verify_password(current_password, current_user.password_hash):
        logger.warning(f"Failed account deletion attempt for user {current_user.username}: incorrect password")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )
    
    try:
        # Delete user
        db.delete(current_user)
        db.commit()
        
        logger.info(f"Account successfully deleted for user {current_user.username}")
        return {"message": "Account deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting account for user {current_user.username}: {str(e)}", exc_info=True)
        raise