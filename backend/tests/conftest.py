import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database import get_db, Base
from app.models import User, Vendor, GiftCard
from app.security import get_password_hash, create_access_token

# Create a test database in memory
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session for testing
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after the test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    # Override the get_db dependency to use the test database
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db):
    """Create a test user and return it"""
    user = User(
        user_id="test_user_id",
        username="testuser",
        password_hash=get_password_hash("Password123"),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        date_of_birth="1990-01-01"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_vendor(db):
    """Create a test vendor and return it"""
    vendor = Vendor(
        vendor_id="test_vendor_id",
        company_name="Test Company",
        company_logo=None
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@pytest.fixture(scope="function")
def test_gift_card(db, test_user, test_vendor):
    """Create a test gift card and return it"""
    gift_card = GiftCard(
        card_id="test_card_id",
        user_id=test_user.user_id,
        vendor_id=test_vendor.vendor_id,
        card_number="1234567890",
        pin="1234",
        balance=100.00,
        expiration_date="2025-12-31",
        front_image=None,
        back_image=None
    )
    db.add(gift_card)
    db.commit()
    db.refresh(gift_card)
    return gift_card


@pytest.fixture(scope="function")
def token(test_user):
    """Create a test token for the test user"""
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture(scope="function")
def authorized_client(client, token):
    """Create a client with authorization header"""
    client.headers = {
        "Authorization": f"Bearer {token}",
        **client.headers
    }
    return client