"""
Invoice model for managing customer invoices.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, Field
import enum

from invoice_app.db.base import Base

class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    REMINDER_SENT = "reminder_sent"
    CANCELLED = "cancelled"

class InvoiceDB(Base):
    """Invoice database model."""

    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String(36), index=True, nullable=False)
    customer_id = Column(String(36), ForeignKey('customers.id'), nullable=False)
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(20), default=InvoiceStatus.DRAFT.value)
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=20.00)
    total = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text)
    recipient_email = Column(String(255))
    currency_code = Column(String(3), default="USD")
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
    id: Optional[str] = None

    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    invoice_number: str
    user_id: str
    customer_id: str
    issue_date: datetime
    due_date: datetime
    status: InvoiceStatus
    subtotal: float
    tax: float
    tax_rate: Optional[float] = 20.0
    total: float
    notes: Optional[str] = None
    recipient_email: Optional[str] = None
    currency_code: Optional[str] = "USD"

    class Config:
        # This allows using strings for enum values
        use_enum_values = True

class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemBase]

class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = None
    customer_id: Optional[str] = None
    issue_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: Optional[InvoiceStatus] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    tax_rate: Optional[float] = None
    total: Optional[float] = None
    notes: Optional[str] = None
    recipient_email: Optional[str] = None
    currency_code: Optional[str] = None
    items: Optional[List[InvoiceItemBase]] = None

    class Config:
        # This allows using strings for enum values
        use_enum_values = True

class Invoice(InvoiceBase):
    id: str
    created_at: datetime
    updated_at: datetime
    items: List[InvoiceItem] = []

    class Config:
        from_attributes = True