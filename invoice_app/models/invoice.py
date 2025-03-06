"""
Invoice model for managing customer invoices.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Text, Enum, Float, func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
import enum

from invoice_app.db.base import Base

class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"

class InvoiceDB(Base):
    """Invoice database model."""
    
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    subtotal = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    notes = Column(String(1000))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship to Customer
    customer = relationship("CustomerDB", back_populates="invoices")
    
    # Relationship to Invoice Items (if you have them)
    items = relationship("InvoiceItemDB", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceItemDB(Base):
    """Invoice item database model."""
    
    __tablename__ = "invoice_items"

    id = Column(String(36), primary_key=True, index=True)
    invoice_id = Column(String(36), ForeignKey('invoices.id'), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)

    # Relationships
    invoice = relationship("InvoiceDB", back_populates="items")

# Pydantic models for API
class InvoiceItemBase(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float

class InvoiceItem(InvoiceItemBase):
    id: str

    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    invoice_number: str
    issue_date: datetime
    due_date: datetime
    status: InvoiceStatus
    subtotal: float
    tax: float
    total: float
    notes: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    customer_id: str

class InvoiceUpdate(InvoiceBase):
    pass

class Invoice(InvoiceBase):
    id: str
    customer_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 