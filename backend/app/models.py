from sqlalchemy import Column, String, Date, DateTime, DECIMAL, ForeignKey, TIMESTAMP, BLOB, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(String(36), primary_key=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    last_login = Column(DateTime)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=func.now())
    
    gift_cards = relationship('GiftCard', back_populates='user')

class Vendor(Base):
    __tablename__ = 'vendors'
    
    vendor_id = Column(String(36), primary_key=True)
    company_name = Column(String(100), nullable=False, unique=True, index=True)
    company_logo = Column(BLOB)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=func.now())
    
    gift_cards = relationship('GiftCard', back_populates='vendor')

class GiftCard(Base):
    __tablename__ = 'gift_cards'
    
    card_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    vendor_id = Column(String(36), ForeignKey('vendors.vendor_id'), nullable=False)
    card_number = Column(String(50), nullable=False, unique=True, index=True)
    pin = Column(String(10))
    balance = Column(DECIMAL(10, 2), nullable=False)
    expiration_date = Column(Date)
    front_image = Column(BLOB)
    back_image = Column(BLOB)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=func.now())
    
    user = relationship('User', back_populates='gift_cards')
    vendor = relationship('Vendor', back_populates='gift_cards')

# Event listeners to update the updated_at column
def before_update_listener(mapper, connection, target):
    target.updated_at = func.now()

event.listen(User, 'before_update', before_update_listener)
event.listen(Vendor, 'before_update', before_update_listener)
event.listen(GiftCard, 'before_update', before_update_listener)