# auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date
import uuid
from pydantic import BaseModel, EmailStr, constr, validator

from .database import get_db
from .models import User
from .security import (
    Token,
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user
)
from .logger import setup_logger
# Initialize logger
logger = setup_logger(__name__, "auth.log")

# Add router path
router = APIRouter(prefix="/auth", tags=["authentication"])


class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    password: constr(min_length=8)
    email: EmailStr
    first_name: constr(min_length=1, max_length=50)
    last_name: constr(min_length=1, max_length=50)
    date_of_birth: date

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    date_of_birth: date
    created_at: datetime

    class Config:
        from_attributes = True

#User registration
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Attempting to register new user: {user.username}")
    try:
        # Hash the password
        logger.debug(f"Hashing password for {user.username}")
        hashed_password = get_password_hash(user.password)
        
        # Create new user instance
        logger.debug(f"Creating new user instance for {user.username}")
        db_user = User(
            user_id=str(uuid.uuid4()),
            username=user.username,
            password_hash=hashed_password,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            date_of_birth=user.date_of_birth
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Successfully registered user: {user.username}")
        return db_user
        
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e).lower()
        logger.error(f"Registration failed due to integrity error: {error_msg}")
        
        if "username" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        elif "email" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed"
        )
    except Exception as e:
        logger.critical(f"Unexpected error during user registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

#Generate user access toekn
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    logger.info(f"Login attempt for user: {form_data.username}")
    
    # Find user
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Update last login
        logger.debug(f"Updating last login time for user: {user.username}")
        user.last_login = datetime.utcnow()
        #user.last_login = datetime.now(datetime.timezone.utc)
        db.commit()
        
        # Create tokens
        logger.debug(f"Generating access and refresh tokens for user: {user.username}")
        access_token = create_access_token(data={"sub": user.username})
        refresh_token = create_refresh_token(data={"sub": user.username})
        
        logger.info(f"Successful login for user: {user.username}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Error during token generation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login process failed"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Token refresh requested for user: {current_user.username}")
    try:
        # Create new tokens
        logger.debug(f"Generating new tokens for user: {current_user.username}")
        access_token = create_access_token(data={"sub": current_user.username})
        refresh_token = create_refresh_token(data={"sub": current_user.username})
        
        logger.info(f"Successfully refreshed tokens for user: {current_user.username}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Error during token refresh: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    logger.info(f"Logout request for user: {current_user.username}")
    # In a more complex implementation, you might want to blacklist the token
    logger.debug(f"Successfully logged out user: {current_user.username}")
    return {"message": "Successfully logged out"}