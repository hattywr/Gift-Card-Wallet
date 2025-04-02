# auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid

from .database import get_db
from .models import User
from .security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_current_user,
    blacklist_token,
    oauth2_scheme
)
from .schemas import UserCreate, UserResponse, Token
from .logger import setup_logger

# Initialize logger
logger = setup_logger(__name__, "auth.log")

# Add router path
router = APIRouter(prefix="/auth", tags=["authentication"])

#User registration
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
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

#Generate user access token
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Get access and refresh tokens with username and password"""
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
    """Get new access and refresh tokens using current authentication"""
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
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    """Logout current user (blacklists the token)"""
    logger.info(f"Logout request for user: {current_user.username}")
    
    # Blacklist the current token
    blacklist_token(token)
    
    logger.info(f"Successfully logged out user: {current_user.username}")
    return {"message": "Successfully logged out"}