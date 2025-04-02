# vendors.py
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Response, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from pydantic import BaseModel, constr
from datetime import datetime
import uuid

from ..database import get_db
from ..models import User, Vendor
from ..security import get_current_user
from ..logger import setup_logger

# Initialize logger
logger = setup_logger(__name__, "main.log")

router = APIRouter(prefix="/vendors", tags=["vendors"])

# Pydantic models for request/response
class VendorCreate(BaseModel):
    company_name: constr(min_length=1, max_length=100)

class VendorResponse(BaseModel):
    vendor_id: str
    company_name: str
    created_at: datetime
    has_logo: bool

    class Config:
        from_attributes = True

@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
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

@router.get("", response_model=List[VendorResponse])
async def list_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all vendors with pagination and optional search"""
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
        
        return vendors
    except Exception as e:
        logger.error(f"Error listing vendors: {str(e)}", exc_info=True)
        raise

@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific vendor by ID"""
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

@router.get("/{vendor_id}/logo")
async def get_vendor_logo(
    vendor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the logo for a specific vendor"""
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

@router.put("/{vendor_id}/logo")
async def update_vendor_logo(
    vendor_id: str,
    logo: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the logo for a specific vendor"""
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