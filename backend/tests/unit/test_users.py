import pytest
from fastapi import status

def test_get_current_user_profile(authorized_client, test_user):
    """Test getting current user profile"""
    response = authorized_client.get("/users/me")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert data["first_name"] == test_user.first_name
    assert data["last_name"] == test_user.last_name


def test_get_user_profile_by_id(authorized_client, test_user):
    """Test getting user profile by ID"""
    response = authorized_client.get(f"/users/{test_user.user_id}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email


def test_get_other_user_profile_forbidden(authorized_client):
    """Test that getting another user's profile is forbidden"""
    response = authorized_client.get("/users/other_user_id")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_user_profile(authorized_client, test_user):
    """Test updating user profile"""
    update_data = {
        "email": "updated@example.com",
        "first_name": "Updated",
        "last_name": "User"
    }
    
    response = authorized_client.put("/users/me", json=update_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == update_data["email"]
    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == update_data["last_name"]
    
    # Ensure username wasn't changed
    assert data["username"] == test_user.username


def test_update_password(authorized_client):
    """Test updating password"""
    password_data = {
        "current_password": "Password123",
        "new_password": "NewPassword123"
    }
    
    response = authorized_client.put("/users/me/password", json=password_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Password updated successfully"
    
    # Test login with new password
    response = authorized_client.post(
        "/auth/token",
        data={"username": "testuser", "password": "NewPassword123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == status.HTTP_200_OK


def test_update_password_wrong_current(authorized_client):
    """Test updating password with wrong current password"""
    password_data = {
        "current_password": "WrongPassword",
        "new_password": "NewPassword123"
    }
    
    response = authorized_client.put("/users/me/password", json=password_data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST