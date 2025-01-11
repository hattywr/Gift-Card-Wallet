# main.py
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Response, Form, Query, Request
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
from .logger import setup_logger

# Initialize logger
logger = setup_logger(__name__, "main.log")

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

@app.get("/")
async def root():
    """Root endpoint that returns a welcome message"""
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Gift Card Wallet API"}

@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running"""
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy"}

@app.get("/db-health")
async def db_health_check(db: Session = Depends(get_db)):
    """Database health check endpoint to verify database connectivity"""
    logger.info("Database health check initiated")
    try:
        db.execute(text("SELECT 1"))
        logger.info("Database health check successful")
        return {"status": "Database connection successful"}
    except Exception as e:
        error_msg = f"Database health check failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"status": "Database connection failed", "error": str(e)}

@app.get("/db-schema")
async def db_schema():
    """Endpoint to retrieve the database schema"""
    logger.info("Database schema retrieval initiated")
    try:
        inspector = inspect(engine)
        schema = {}
        tables = inspector.get_table_names()
        logger.debug(f"Found {len(tables)} tables in database")
        
        for table_name in tables:
            logger.debug(f"Inspecting table: {table_name}")
            columns = inspector.get_columns(table_name)
            schema[table_name] = [
                {"name": column["name"], "type": str(column["type"])} 
                for column in columns
            ]
            logger.debug(f"Table {table_name}: {len(columns)} columns retrieved")
        
        logger.info("Database schema retrieved successfully")
        return schema
    except Exception as e:
        error_msg = f"Failed to retrieve database schema: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise
    
@app.post("/vendors", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    company_name: str = Form(...),
    logo: Optional[UploadFile] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new vendor with optional logo upload"""
    logger.info(f"Creating new vendor '{company_name}' by user {current_user.username}")
    try:
        # Process logo if provided
        logo_data = None
        if logo:
            logger.debug(f"Processing logo upload for vendor '{company_name}'")
            if not logo.content_type.startswith('image/'):
                logger.warning(f"Invalid file type uploaded for vendor '{company_name}': {logo.content_type}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be an image"
                )
            logo_data = await logo.read()
            logger.debug(f"Logo successfully processed for vendor '{company_name}'")
            
        # Create vendor
        db_vendor = Vendor(
            vendor_id=str(uuid.uuid4()),
            company_name=company_name,
            company_logo=logo_data
        )
        
        db.add(db_vendor)
        db.commit()
        db.refresh(db_vendor)
        
        logger.info(f"Vendor '{company_name}' successfully created with ID: {db_vendor.vendor_id}")
        db_vendor.has_logo = db_vendor.company_logo is not None
        return db_vendor
        
    except IntegrityError:
        db.rollback()
        logger.error(f"Failed to create vendor '{company_name}': Company name already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name already exists"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating vendor '{company_name}': {str(e)}", exc_info=True)
        raise

@app.get("/vendors", response_model=PaginatedResponse[VendorResponse])
async def list_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Listing vendors - Page: {page}, Size: {page_size}, Search: {search}")
    try:
        query = db.query(Vendor)
        
        if search:
            logger.debug(f"Applying search filter: {search}")
            query = query.filter(Vendor.company_name.ilike(f"%{search}%"))
        
        total = query.count()
        logger.debug(f"Total vendors found: {total}")
        
        vendors = query.offset((page - 1) * page_size).limit(page_size).all()
        logger.debug(f"Retrieved {len(vendors)} vendors for current page")
        
        for vendor in vendors:
            vendor.has_logo = vendor.company_logo is not None
        
        return {
            "items": vendors,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        logger.error(f"Error listing vendors: {str(e)}", exc_info=True)
        raise

@app.get("/vendors/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Retrieving vendor with ID: {vendor_id}")
    try:
        vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
        if not vendor:
            logger.warning(f"Vendor not found with ID: {vendor_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        vendor.has_logo = vendor.company_logo is not None
        logger.debug(f"Successfully retrieved vendor: {vendor.company_name}")
        return vendor
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving vendor {vendor_id}: {str(e)}", exc_info=True)
        raise

@app.get("/vendors/{vendor_id}/logo")
async def get_vendor_logo(
    vendor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Retrieving logo for vendor ID: {vendor_id}")
    try:
        vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
        if not vendor or not vendor.company_logo:
            logger.warning(f"Logo not found for vendor ID: {vendor_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Logo not found"
            )
        logger.debug(f"Successfully retrieved logo for vendor: {vendor.company_name}")
        return Response(content=vendor.company_logo, media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving logo for vendor {vendor_id}: {str(e)}", exc_info=True)
        raise

@app.put("/vendors/{vendor_id}/logo")
async def update_vendor_logo(
    vendor_id: str,
    logo: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Updating logo for vendor ID: {vendor_id} by user {current_user.username}")
    
    if not logo.content_type.startswith('image/'):
        logger.warning(f"Invalid file type uploaded for vendor {vendor_id}: {logo.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    if not vendor:
        logger.warning(f"Attempted to update logo for non-existent vendor: {vendor_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    try:
        logger.debug(f"Reading new logo file for vendor: {vendor.company_name}")
        vendor.company_logo = await logo.read()
        db.commit()
        logger.info(f"Successfully updated logo for vendor: {vendor.company_name}")
        return {"message": "Logo updated successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update logo for vendor {vendor_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update logo"
        )

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
    logger.info(f"Creating new gift card for user {user_id} with vendor {vendor_id}")
    
    # Verify permissions
    if current_user.user_id != user_id:
        logger.warning(f"Unauthorized attempt to create gift card: User {current_user.user_id} tried to create card for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create gift cards for other users"
        )

    # Verify vendor exists
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    if not vendor:
        logger.warning(f"Attempted to create gift card with non-existent vendor: {vendor_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )

    # Validate balance
    if balance <= 0:
        logger.warning(f"Invalid balance amount attempted: {balance}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Balance must be greater than 0"
        )

    try:
        # Process images
        front_image_data = None
        back_image_data = None

        if front_image:
            logger.debug("Processing front image upload")
            if not front_image.content_type.startswith('image/'):
                logger.warning(f"Invalid front image type: {front_image.content_type}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Front image must be an image file"
                )
            front_image_data = await front_image.read()
            logger.debug("Front image processed successfully")

        if back_image:
            logger.debug("Processing back image upload")
            if not back_image.content_type.startswith('image/'):
                logger.warning(f"Invalid back image type: {back_image.content_type}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Back image must be an image file"
                )
            back_image_data = await back_image.read()
            logger.debug("Back image processed successfully")

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

        logger.info(f"Successfully created gift card {gift_card.card_id} for user {user_id}")
        logger.debug(f"Gift card details: Vendor: {vendor.company_name}, Balance: {balance}, Expiration: {expiration_date}")
        
        return gift_card

    except IntegrityError as e:
        db.rollback()
        if "card_number" in str(e).lower():
            logger.error(f"Duplicate card number attempted: {card_number}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Card number already exists"
            )
        logger.error(f"Gift card creation failed due to integrity error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gift card creation failed"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating gift card: {str(e)}", exc_info=True)
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
    logger.info(f"Retrieving gift cards for user {user_id}")
    logger.debug(f"Query parameters - Page: {page}, Size: {page_size}, Search: {search}")

    # Verify user has access
    if current_user.user_id != user_id:
        logger.warning(f"Unauthorized access attempt: User {current_user.user_id} tried to access gift cards of user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these gift cards"
        )
    
    try:
        # Build query
        query = db.query(GiftCard, Vendor.company_name)\
            .join(Vendor, GiftCard.vendor_id == Vendor.vendor_id)\
            .filter(GiftCard.user_id == user_id)
        
        if search:
            logger.debug(f"Applying search filter: {search}")
            query = query.filter(
                or_(
                    GiftCard.card_number.ilike(f"%{search}%"),
                    Vendor.company_name.ilike(f"%{search}%")
                )
            )
        
        total = query.count()
        logger.debug(f"Total gift cards found: {total}")
        
        results = query.offset((page - 1) * page_size).limit(page_size).all()
        logger.debug(f"Retrieved {len(results)} gift cards for current page")
        
        gift_cards = []
        for gift_card, vendor_name in results:
            gift_card.has_front_image = gift_card.front_image is not None
            gift_card.has_back_image = gift_card.back_image is not None
            gift_card.vendor_name = vendor_name
            gift_cards.append(gift_card)
        
        logger.info(f"Successfully retrieved gift cards for user {user_id}")
        return {
            "items": gift_cards,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        logger.error(f"Error retrieving gift cards for user {user_id}: {str(e)}", exc_info=True)
        raise

@app.get("/gift-cards/{card_id}/images/{image_type}")
async def get_gift_card_image(
    card_id: str,
    image_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get gift card image (front or back)"""
    logger.info(f"Retrieving {image_type} image for gift card {card_id}")

    try:
        gift_card = db.query(GiftCard).filter(GiftCard.card_id == card_id).first()
        if not gift_card:
            logger.warning(f"Gift card not found: {card_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gift card not found"
            )

        # Verify user has access
        if current_user.user_id != gift_card.user_id:
            logger.warning(f"Unauthorized access attempt: User {current_user.user_id} tried to access gift card {card_id} belonging to user {gift_card.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this gift card"
            )

        if image_type not in ['front', 'back']:
            logger.warning(f"Invalid image type requested: {image_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image type must be 'front' or 'back'"
            )

        image = gift_card.front_image if image_type == 'front' else gift_card.back_image
        if not image:
            logger.warning(f"No {image_type} image found for gift card {card_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {image_type} image found"
            )

        logger.info(f"Successfully retrieved {image_type} image for gift card {card_id}")
        return Response(content=image, media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving {image_type} image for gift card {card_id}: {str(e)}", exc_info=True)
        raise

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_msg = f"HTTP {exc.status_code} error occurred. Path: {request.url.path}, Detail: {exc.detail}"
    
    if exc.status_code >= 500:
        logger.error(error_msg)
    elif exc.status_code >= 400:
        logger.warning(error_msg)
    else:
        logger.info(error_msg)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    error_msg = f"Unhandled exception occurred. Path: {request.url.path}, Error: {str(exc)}"
    logger.error(error_msg, exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )