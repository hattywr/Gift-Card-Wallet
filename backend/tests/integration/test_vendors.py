import pytest
import io
from fastapi import status
from PIL import Image
import numpy as np

def create_test_logo():
    """Create a simple test logo image"""
    img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def test_create_vendor(authorized_client):
    """Test creating a vendor"""
    # Create test logo
    logo = create_test_logo()
    
    # Create form data
    form_data = {
        "company_name": "New Test Company"
    }
    
    files = {
        "logo": ("logo.png", logo, "image/png")
    }
    
    response = authorized_client.post(
        "/vendors",
        data=form_data,
        files=files
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["company_name"] == form_data["company_name"]
    assert data["has_logo"] is True
    assert "vendor_id" in data


def test_list_vendors(authorized_client, test_vendor):
    """Test listing vendors"""
    response = authorized_client.get("/vendors")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    assert any(vendor["vendor_id"] == test_vendor.vendor_id for vendor in data)


def test_get_vendor(authorized_client, test_vendor):
    """Test getting a specific vendor"""
    response = authorized_client.get(f"/vendors/{test_vendor.vendor_id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["vendor_id"] == test_vendor.vendor_id
    assert data["company_name"] == test_vendor.company_name


def test_update_vendor_logo(authorized_client, test_vendor):
    """Test updating a vendor logo"""
    # Create new test logo
    logo = create_test_logo()
    
    files = {
        "logo": ("new_logo.png", logo, "image/png")
    }
    
    response = authorized_client.put(
        f"/vendors/{test_vendor.vendor_id}/logo",
        files=files
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Logo updated successfully"
    
    # Verify logo was updated by getting vendor
    response = authorized_client.get(f"/vendors/{test_vendor.vendor_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["has_logo"] is True


def test_get_vendor_logo(authorized_client, db, test_vendor):
    """Test getting a vendor logo"""
    # First, add a logo to the test vendor
    test_vendor.company_logo = create_test_logo().read()
    db.commit()
    
    response = authorized_client.get(f"/vendors/{test_vendor.vendor_id}/logo")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


def test_get_nonexistent_vendor(authorized_client):
    """Test getting a non-existent vendor"""
    response = authorized_client.get("/vendors/nonexistent_id")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND