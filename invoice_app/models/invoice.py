"""
Invoice model for managing customer invoices.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
import enum

from invoice_app.db.base import Base

class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class InvoiceDB(Base):
    """Invoice database model."""

    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey('customers.id'), nullable=False)
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(20), default=InvoiceStatus.DRAFT.value)
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text)
    recipient_email = Column(String(255))  # New field for recipient email
    currency_code = Column(String(3), default="USD")  # New field for currency
    recipient_email = Column(String(255))  # New field for recipient email
    currency_code = Column(String(3), default="USD")  # New field for currency
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("CustomerDB", back_populates="invoices")
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

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItem(InvoiceItemBase):
    id: str

    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    invoice_number: str
    customer_id: str
    issue_date: datetime
    due_date: datetime
    status: str
    subtotal: float
    tax: float
    total: float
    notes: Optional[str] = None
    recipient_email: Optional[str] = None  # New field for recipient email
    currency_code: Optional[str] = "USD"  # New field for currency
    recipient_email: Optional[str] = None  # New field for recipient email
    currency_code: Optional[str] = "USD"  # New field for currency

class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemBase]

class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    recipient_email: Optional[str] = None  # New field for recipient email
    currency_code: Optional[str] = "USD"  # New field for currency
    due_date: Optional[datetime] = None
    recipient_email: Optional[str] = None
    currency_code: Optional[str] = None

class Invoice(InvoiceBase):
    id: str
    created_at: datetime
    updated_at: datetime
    items: List[InvoiceItem] = []

    class Config:
        from_attributes = True