# main.py
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Response, Form, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect, or_
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Any, Generic, TypeVar
from pydantic import BaseModel, constr
from datetime import date, datetime
import uuid
from decimal import Decimal

from .database import engine, get_db
from .models import Base, GiftCard, User, Vendor
from .security import (
    rate_limit_middleware,
    validation_middleware,
    get_current_user
)
from .auth import router as auth_router
from .config import get_settings

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(validation_middleware)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_router)

# Define TypeVar for generic pagination
T = TypeVar('T')

# Pydantic models for request/response
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

    class Config:
        from_attributes = True

class VendorCreate(BaseModel):
    company_name: constr(min_length=1, max_length=100)

class VendorResponse(BaseModel):
    vendor_id: str
    company_name: str
    created_at: datetime
    has_logo: bool

    class Config:
        from_attributes = True

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

# Basic endpoints
@app.get("/")
async def root():
    return {"message": "Welcome to Gift Card Wallet API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/db-health")
async def db_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "Database connection successful"}
    except Exception as e:
        return {"status": "Database connection failed", "error": str(e)}

@app.get("/db-schema")
async def db_schema():
    inspector = inspect(engine)
    schema = {}
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        schema[table_name] = [{"name": column["name"], "type": str(column["type"])} for column in columns]
    return schema

# Vendor endpoints
@app.post("/vendors", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    company_name: str = Form(...),
    logo: Optional[UploadFile] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new vendor with optional logo upload"""
    try:
        # Process logo if provided
        logo_data = None
        if logo:
            if not logo.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be an image"
                )
            logo_data = await logo.read()
            
        # Create vendor
        db_vendor = Vendor(
            vendor_id=str(uuid.uuid4()),
            company_name=company_name,
            company_logo=logo_data
        )
        
        db.add(db_vendor)
        db.commit()
        db.refresh(db_vendor)
        
        db_vendor.has_logo = db_vendor.company_logo is not None
        return db_vendor
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name already exists"
        )

@app.get("/vendors", response_model=PaginatedResponse[VendorResponse])
async def list_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Vendor)
    
    if search:
        query = query.filter(Vendor.company_name.ilike(f"%{search}%"))
    
    total = query.count()
    vendors = query.offset((page - 1) * page_size).limit(page_size).all()
    
    for vendor in vendors:
        vendor.has_logo = vendor.company_logo is not None
    
    return {
        "items": vendors,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }

@app.get("/vendors/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    vendor.has_logo = vendor.company_logo is not None
    return vendor

@app.get("/vendors/{vendor_id}/logo")
async def get_vendor_logo(
    vendor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    if not vendor or not vendor.company_logo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logo not found"
        )
    return Response(content=vendor.company_logo, media_type="image/png")

@app.put("/vendors/{vendor_id}/logo")
async def update_vendor_logo(
    vendor_id: str,
    logo: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not logo.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    try:
        vendor.company_logo = await logo.read()
        db.commit()
        return {"message": "Logo updated successfully"}
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update logo"
        )

# Gift card endpoints
@app.post("/gift-cards", response_model=GiftCardResponse, status_code=status.HTTP_201_CREATED)
async def create_gift_card(
    user_id: str = Form(...),
    vendor_id: str = Form(...),
    card_number: str = Form(...),
    pin: Optional[str] = Form(None),
    balance: Decimal = Form(...),
    expiration_date: Optional[date] = Form(None),
    front_image: Optional[UploadFile] = None,
    back_image: Optional[UploadFile] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify permissions
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create gift cards for other users"
        )

    # Verify vendor exists
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )

    # Validate balance
    if balance <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Balance must be greater than 0"
        )

    try:
        # Process images
        front_image_data = None
        back_image_data = None

        if front_image:
            if not front_image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Front image must be an image file"
                )
            front_image_data = await front_image.read()

        if back_image:
            if not back_image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Back image must be an image file"
                )
            back_image_data = await back_image.read()

        # Create gift card
        gift_card = GiftCard(
            card_id=str(uuid.uuid4()),
            user_id=user_id,
            vendor_id=vendor_id,
            card_number=card_number,
            pin=pin,
            balance=balance,
            expiration_date=expiration_date,
            front_image=front_image_data,
            back_image=back_image_data
        )

        db.add(gift_card)
        db.commit()
        db.refresh(gift_card)

        # Add additional response fields
        gift_card.has_front_image = gift_card.front_image is not None
        gift_card.has_back_image = gift_card.back_image is not None
        gift_card.vendor_name = vendor.company_name

        return gift_card

    except IntegrityError as e:
        db.rollback()
        if "card_number" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Card number already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gift card creation failed"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/users/{user_id}/gift-cards", response_model=PaginatedResponse[GiftCardResponse])
async def get_user_gift_cards(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify user has access
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these gift cards"
        )
    
    # Build query
    query = db.query(GiftCard, Vendor.company_name)\
        .join(Vendor, GiftCard.vendor_id == Vendor.vendor_id)\
        .filter(GiftCard.user_id == user_id)
    
    if search:
        query = query.filter(
            or_(
                GiftCard.card_number.ilike(f"%{search}%"),
                Vendor.company_name.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()
    
    gift_cards = []
    for gift_card, vendor_name in results:
        gift_card.has_front_image = gift_card.front_image is not None
        gift_card.has_back_image = gift_card.back_image is not None
        gift_card.vendor_name = vendor_name
        gift_cards.append(gift_card)
    
    return {
        "items": gift_cards,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }

@app.get("/gift-cards/{card_id}/images/{image_type}")
async def get_gift_card_image(
    card_id: str,
    image_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get gift card image (front or back)"""
    gift_card = db.query(GiftCard).filter(GiftCard.card_id == card_id).first()
    if not gift_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gift card not found"
        )

    # Verify user has access
    if current_user.user_id != gift_card.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this gift card"
        )

    if image_type not in ['front', 'back']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image type must be 'front' or 'back'"
        )

    image = gift_card.front_image if image_type == 'front' else gift_card.back_image
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {image_type} image found"
        )

    return Response(content=image, media_type="image/png")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )