# security.py
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, Security, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from collections import defaultdict
import time
from datetime import datetime, date
from fastapi.responses import JSONResponse
from .database import get_db
from .models import User
from .config import get_settings
from .logger import setup_logger

# Get settings instance
settings = get_settings()

# Initialize logger
logger = setup_logger(__name__, "security.log")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Token models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Rate limiting
class RateLimiter:
    def __init__(self, requests_per_minute: int = settings.RATE_LIMIT_PER_MINUTE):
        self.requests = defaultdict(list)
        self.requests_per_minute = requests_per_minute
        logger.info(f"RateLimiter initialized with {requests_per_minute} requests per minute")

    def _clean_old_requests(self, client_ip: str):
        now = time.time()
        original_count = len(self.requests[client_ip])
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > now - 60
        ]
        removed_count = original_count - len(self.requests[client_ip])
        if removed_count > 0:
            logger.debug(f"Cleaned {removed_count} old requests for IP {client_ip}")

    def is_rate_limited(self, client_ip: str) -> bool:
        self._clean_old_requests(client_ip)
        is_limited = len(self.requests[client_ip]) >= self.requests_per_minute
        if is_limited:
            logger.warning(f"Rate limit exceeded for IP {client_ip}")
        return is_limited

    def add_request(self, client_ip: str):
        self.requests[client_ip].append(time.time())
        logger.debug(f"Request added for IP {client_ip}. Total requests: {len(self.requests[client_ip])}")

# Create rate limiter instance
rate_limiter = RateLimiter()

# Password functions
def get_password_hash(password: str) -> str:
    logger.debug("Generating password hash")
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    result = pwd_context.verify(plain_password, hashed_password)
    if not result:
        logger.warning("Password verification failed")
    return result

# Token functions
def create_access_token(data: dict) -> str:
    logger.debug(f"Creating access token for user: {data.get('sub')}")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    #expire = datetime.now(datetime.timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

# Refresh Access Token
def create_refresh_token(data: dict) -> str:
    logger.debug(f"Creating refresh token for user: {data.get('sub')}")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.error("Token payload missing username")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        logger.error("Failed to decode JWT token")
        raise credentials_exception
        
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        logger.error(f"User not found: {token_data.username}")
        raise credentials_exception
    
    logger.info(f"Successfully authenticated user: {user.username}")
    return user

# Rate limiting middleware
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    if rate_limiter.is_rate_limited(client_ip):
        logger.warning(f"Rate limit exceeded for IP {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"}
        )
    
    rate_limiter.add_request(client_ip)
    response = await call_next(request)
    return response

# Request validation middleware
async def validation_middleware(request: Request, call_next):
    try:
        # Skip validation for health check endpoints
        if request.url.path in ["/", "/health", "/db-health"]:
            logger.debug(f"Skipping validation for health check endpoint: {request.url.path}")
            return await call_next(request)

        # Skip validation for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            logger.debug("Skipping validation for OPTIONS request")
            return await call_next(request)
            
        # Validate content type for POST/PUT requests with bodies
        if request.method in ["POST", "PUT"]:
            content_type = request.headers.get("content-type", "")
            
            # Skip validation for form data (file uploads)
            if "multipart/form-data" in content_type:
                logger.debug("Skipping content type validation for multipart form data")
                return await call_next(request)
                
            if not content_type:
                logger.error("Missing Content-Type header in request")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Content-Type header is required"}
                )
            
            logger.debug(f"Request validation successful for {request.method} {request.url.path}")
        
        return await call_next(request)
        
    except Exception as e:
        logger.error(f"Error during request validation: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error during request validation"}
        )