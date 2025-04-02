# schemas.py
from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional, List, Generic, TypeVar
from datetime import date, datetime
from decimal import Decimal

T = TypeVar('T')

# User schemas
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

# Vendor schemas
class VendorCreate(BaseModel):
    company_name: constr(min_length=1, max_length=100)

class VendorResponse(BaseModel):
    vendor_id: str
    company_name: str
    created_at: datetime
    has_logo: bool

    class Config:
        from_attributes = True

# Gift card schemas
class GiftCardResponse(BaseModel):
    card_id: str
    user_id: str
    vendor_id: str
    card_number: str
    pin: Optional[str]
    balance: Decimal
    expiration_date: Optional[date]
    has_front_image: bool
    has_back_image: bool
    created_at: datetime
    vendor_name: str

    class Config:
        from_attributes = True

class GiftCardUpdate(BaseModel):
    balance: Decimal

    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Generic pagination response
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

    class Config:
        from_attributes = True