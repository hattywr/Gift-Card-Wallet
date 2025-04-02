import pytest
from fastapi import status
import json

def test_register_user(client):
    """Test user registration"""
    user_data = {
        "username": "newuser",
        "password": "Password123",
        "email": "newuser@example.com",
        "first_name": "New",
        "last_name": "User",
        "date_of_birth": "1990-01-01"
    }
    
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password_hash" not in data  # Ensure password is not returned
    assert data["user_id"] is not None


def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "Password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    """Test login with wrong password"""
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_nonexistent_user(client):
    """Test login with non-existent user"""
    response = client.post(
        "/auth/token",
        data={"username": "nonexistent", "password": "Password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_token(authorized_client):
    """Test token refresh"""
    response = authorized_client.post("/auth/refresh")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_logout(authorized_client):
    """Test logout"""
    response = authorized_client.post("/auth/logout")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Successfully logged out"
    
    # After logout, token should be blacklisted, so next request should fail
    response = authorized_client.get("/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED