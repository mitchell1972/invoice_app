"""
Payment model module.

This module contains the Payment model and related enums for
tracking payments made against invoices.
"""
from datetime import datetime
from typing import Dict, Any, Optional
import enum
import uuid

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class PaymentMethod(enum.Enum):
    """Enum representing payment methods."""
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    CHECK = "check"
    PAYPAL = "paypal"
    OTHER = "other"


class PaymentStatus(enum.Enum):
    """Enum representing payment statuses."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(UUIDMixin, TimestampMixin, Base):
    """
    Payment model representing payments made against invoices.
    """

    __tablename__ = 'payments'

    # Primary key and identifiers
    id = Column(Integer, primary_key=True)

    # Foreign keys and relationships
    invoice_id = Column(Integer, ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)

    # Payment details
    amount = Column(Float, nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False, default=PaymentMethod.OTHER)
    payment_date = Column(DateTime, nullable=False, default=datetime.now, index=True)
    reference = Column(String(100))  # Transaction reference number
    notes = Column(Text)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.COMPLETED)

    # Additional fields
    is_refund = Column(Boolean, default=False)
    refund_reason = Column(Text)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")

    @property
    def formatted_amount(self) -> str:
        """Return formatted amount with currency symbol."""
        # Get currency from invoice if available
        currency = self.invoice.currency if self.invoice else "USD"

        if currency == "USD":
            return f"${self.amount:.2f}"
        elif currency == "EUR":
            return f"€{self.amount:.2f}"
        elif currency == "GBP":
            return f"£{self.amount:.2f}"
        else:
            return f"{self.amount:.2f} {currency}"

    @property
    def payment_method_display(self) -> str:
        """Return human-readable payment method."""
        method_display = {
            PaymentMethod.BANK_TRANSFER: "Bank Transfer",
            PaymentMethod.CREDIT_CARD: "Credit Card",
            PaymentMethod.CASH: "Cash",
            PaymentMethod.CHECK: "Check",
            PaymentMethod.PAYPAL: "PayPal",
            PaymentMethod.OTHER: "Other"
        }
        return method_display.get(self.payment_method, "Other")

    def __repr__(self) -> str:
        return f"<Payment {self.id}: {self.amount} on Invoice {self.invoice_id}>"