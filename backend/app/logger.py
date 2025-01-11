# logger.py
import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from functools import lru_cache

from .config import get_settings

settings = get_settings()

class CustomFormatter(logging.Formatter):
    """Custom formatter that includes colors for different log levels"""
    
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: grey + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.INFO: grey + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

@lru_cache()
def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with both console and file handlers.
    Args:
        name: The name of the logger (usually __name__)
        log_file: Optional file path for logging. If None, only console logging is used.
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set base logging level
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_dir / log_file,
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

# Example usage in auth.py:
def auth_logger_example():
    """Example of how to implement the logger in a function"""
    from auth import router  # Update with your actual import path
    
    # Get logger for this module
    logger = setup_logger(__name__, "auth.log")
    
    @router.post("/register")
    async def register_user(user: UserCreate, db: Session = Depends(get_db)):
        try:
            logger.info(f"Attempting to register new user: {user.username}")
            
            # Hash the password
            hashed_password = get_password_hash(user.password)
            logger.debug("Password hashed successfully")
            
            # Create new user instance
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
            logger.error(f"Registration failed due to integrity error: {str(e)}")
            if "username" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
            elif "email" in str(e).lower():
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