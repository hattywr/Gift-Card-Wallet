# gift_cards.py
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Response, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
import uuid

from ..database import get_db
from ..models import User, Vendor, GiftCard
from ..security import get_current_user
from ..logger import setup_logger

# Initialize logger
logger = setup_logger(__name__, "main.log")

router = APIRouter(tags=["gift_cards"])

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

@router.post("/gift-cards", response_model=GiftCardResponse, status_code=status.HTTP_201_CREATED)
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
    """Create a new gift card with optional images"""
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

@router.get("/users/{user_id}/gift-cards", response_model=PaginatedResponse[GiftCardResponse])
async def get_user_gift_cards(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all gift cards for a specific user with pagination and search"""
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

@router.get("/gift-cards/{card_id}", response_model=GiftCardResponse)
async def get_gift_card(
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific gift card by ID"""
    logger.info(f"Retrieving gift card with ID: {card_id}")
    
    try:
        # Get gift card with vendor name
        result = db.query(GiftCard, Vendor.company_name)\
            .join(Vendor, GiftCard.vendor_id == Vendor.vendor_id)\
            .filter(GiftCard.card_id == card_id)\
            .first()
        
        if not result:
            logger.warning(f"Gift card not found with ID: {card_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gift card not found"
            )
        
        gift_card, vendor_name = result
        
        # Verify user has access
        if current_user.user_id != gift_card.user_id:
            logger.warning(f"Unauthorized access attempt: User {current_user.user_id} tried to access gift card {card_id} belonging to user {gift_card.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this gift card"
            )
        
        # Add additional fields for response
        gift_card.has_front_image = gift_card.front_image is not None
        gift_card.has_back_image = gift_card.back_image is not None
        gift_card.vendor_name = vendor_name
        
        logger.info(f"Successfully retrieved gift card {card_id}")
        return gift_card
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving gift card {card_id}: {str(e)}", exc_info=True)
        raise

@router.put("/gift-cards/{card_id}/balance", response_model=GiftCardResponse)
async def update_gift_card_balance(
    card_id: str,
    update_data: GiftCardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the balance of a gift card"""
    logger.info(f"Updating balance for gift card {card_id} to {update_data.balance}")
    
    try:
        # Get gift card with vendor name
        result = db.query(GiftCard, Vendor.company_name)\
            .join(Vendor, GiftCard.vendor_id == Vendor.vendor_id)\
            .filter(GiftCard.card_id == card_id)\
            .first()
        
        if not result:
            logger.warning(f"Gift card not found with ID: {card_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gift card not found"
            )
        
        gift_card, vendor_name = result
        
        # Verify user has access
        if current_user.user_id != gift_card.user_id:
            logger.warning(f"Unauthorized access attempt: User {current_user.user_id} tried to update gift card {card_id} belonging to user {gift_card.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this gift card"
            )
        
        # Validate new balance
        if update_data.balance < 0:
            logger.warning(f"Invalid balance amount attempted: {update_data.balance}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Balance cannot be negative"
            )
        
        # Update balance
        gift_card.balance = update_data.balance
        db.commit()
        db.refresh(gift_card)
        
        # Add additional fields for response
        gift_card.has_front_image = gift_card.front_image is not None
        gift_card.has_back_image = gift_card.back_image is not None
        gift_card.vendor_name = vendor_name
        
        logger.info(f"Successfully updated balance for gift card {card_id} to {update_data.balance}")
        return gift_card
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating balance for gift card {card_id}: {str(e)}", exc_info=True)
        raise

@router.get("/gift-cards/{card_id}/images/{image_type}")
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