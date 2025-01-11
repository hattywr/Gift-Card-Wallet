# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache  # Added this import
import os

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Gift Card Wallet API"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React frontend default
        "http://localhost:8000",  # Local development
    ]
    
    # Database
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "gift_card_wallet")
    
    # Database Pool Settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif"]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

@lru_cache()
def get_settings() -> Settings:
    """
    Creates a cached instance of settings.
    Use this function to get settings throughout the application.
    """
    return Settings()

# Example .env file template
ENV_TEMPLATE = """
# Application
DEBUG=False

# Security
JWT_SECRET_KEY=your-super-secret-key-change-in-production

# Database
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=gift_card_wallet

# CORS (comma-separated list)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
"""

def generate_env_template():
    """
    Generates a template .env file if it doesn't exist
    """
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(ENV_TEMPLATE.strip())
        print("Generated .env template file")

def validate_env():
    """
    Validates that all required environment variables are set
    """
    settings = get_settings()
    
    # Check database configuration
    if not all([settings.DB_USER, settings.DB_PASSWORD, settings.DB_HOST, 
                settings.DB_PORT, settings.DB_NAME]):
        raise ValueError("Missing required database configuration")
    
    # Check security configuration
    if settings.JWT_SECRET_KEY == "your-super-secret-key-change-in-production":
        print("WARNING: Using default JWT secret key. Change this in production!")
    
    # Check CORS configuration
    if not settings.CORS_ORIGINS:
        raise ValueError("CORS_ORIGINS must not be empty")
    
    return True

# Usage example:
if __name__ == "__main__":
    # Generate template if needed
    generate_env_template()
    
    # Validate environment
    try:
        validate_env()
        print("Environment validation successful")
    except ValueError as e:
        print(f"Environment validation failed: {str(e)}")