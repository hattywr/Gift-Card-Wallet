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
from fastapi.responses import JSONResponse
from .database import get_db
from .models import User
from .config import get_settings

# Get settings instance
settings = get_settings()

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

    def _clean_old_requests(self, client_ip: str):
        now = time.time()
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > now - 60
        ]

    def is_rate_limited(self, client_ip: str) -> bool:
        self._clean_old_requests(client_ip)
        return len(self.requests[client_ip]) >= self.requests_per_minute

    def add_request(self, client_ip: str):
        self.requests[client_ip].append(time.time())

# Create rate limiter instance
rate_limiter = RateLimiter()

# Password functions
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Token functions
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
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
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# Rate limiting middleware
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    if rate_limiter.is_rate_limited(client_ip):
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
            return await call_next(request)

        # Skip validation for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
            
        # Validate content type for POST/PUT requests with bodies
        if request.method in ["POST", "PUT"]:
            content_type = request.headers.get("content-type", "")
            
            # Skip validation for form data (file uploads)
            if "multipart/form-data" in content_type:
                return await call_next(request)
                
            if not content_type:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Content-Type header is required"}
                )
                
            # Additional content type validation can be added here
        
        return await call_next(request)
        
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error during request validation"}
        )