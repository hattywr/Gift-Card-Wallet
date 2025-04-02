import pytest
import io
from fastapi import status
from PIL import Image
import numpy as np

def create_test_image():
    """Create a simple test image"""
    img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def test_create_gift_card(authorized_client, test_user, test_vendor):
    """Test creating a gift card"""
    # Create test images
    front_image = create_test_image()
    back_image = create_test_image()
    
    # Create form data
    form_data = {
        "user_id": test_user.user_id,
        "vendor_id": test_vendor.vendor_id,
        "card_number": "9876543210",
        "pin": "5678",
        "balance": "50.75",
        "expiration_date": "2024-12-31"
    }
    
    files = {
        "front_image": ("front.png", front_image, "image/png"),
        "back_image": ("back.png", back_image, "image/png")
    }
    
    response = authorized_client.post(
        "/gift-cards",
        data=form_data,
        files=files
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["card_number"] == form_data["card_number"]
    assert data["pin"] == form_data["pin"]
    assert float(data["balance"]) == float(form_data["balance"])
    assert data["has_front_image"] is True
    assert data["has_back_image"] is True
    assert data["vendor_name"] == test_vendor.company_name


def test_get_user_gift_cards(authorized_client, test_user, test_gift_card):
    """Test getting all gift cards for a user"""
    response = authorized_client.get(f"/users/{test_user.user_id}/gift-cards")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["card_id"] == test_gift_card.card_id
    assert data["items"][0]["card_number"] == test_gift_card.card_number


def test_get_gift_card(authorized_client, test_gift_card):
    """Test getting a specific gift card"""
    response = authorized_client.get(f"/gift-cards/{test_gift_card.card_id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["card_id"] == test_gift_card.card_id
    assert data["card_number"] == test_gift_card.card_number
    assert float(data["balance"]) == float(test_gift_card.balance)


def test_update_gift_card_balance(authorized_client, test_gift_card):
    """Test updating a gift card balance"""
    new_balance = 75.50
    update_data = {"balance": new_balance}
    
    response = authorized_client.put(
        f"/gift-cards/{test_gift_card.card_id}/balance",
        json=update_data
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert float(data["balance"]) == new_balance


def test_access_other_user_gift_card_forbidden(authorized_client, db):
    """Test that accessing another user's gift card is forbidden"""
    # Create a gift card for another user
    other_gift_card = {
        "card_id": "other_card_id",
        "user_id": "other_user_id",  # Different from test_user
        "vendor_id": "test_vendor_id",
        "card_number": "5555555555",
        "balance": 100.00
    }
    
    # Try to access the other user's gift card
    response = authorized_client.get(f"/gift-cards/{other_gift_card['card_id']}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND