"""
Customer model representing a business client.
"""
from typing import Optional, List
from datetime import datetime
import re
from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.orm import validates, relationship
from pydantic import BaseModel, EmailStr

from invoice_app.db.base import Base

# SQLAlchemy Model
class CustomerDB(Base):
    """Customer database model."""
    
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    company = Column(String(100))
    phone = Column(String(20))
    address = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Use string reference to avoid circular import
    invoices = relationship("InvoiceDB", back_populates="customer", cascade="all, delete-orphan")

    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")
        return email

# Pydantic models for API
class CustomerBase(BaseModel):
    """Shared customer properties."""
    name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None

class CustomerCreate(CustomerBase):
    """Properties to receive on customer creation."""
    pass

class CustomerUpdate(CustomerBase):
    """Properties to receive on customer update."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class CustomerInDBBase(CustomerBase):
    """Properties shared by models stored in DB."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Customer(CustomerInDBBase):
    """Properties to return to client."""
    total_invoices: Optional[int] = None
    total_revenue: Optional[float] = None 