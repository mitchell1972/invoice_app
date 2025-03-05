"""
Invoice model representing a business invoice.

This module defines the Invoice class which is central to the invoicing
application, storing all information related to customer invoices.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, Any, List, Optional
import uuid

from invoice_app.models.base import BaseModel
from invoice_app.models.invoice_item import InvoiceItem


class InvoiceStatus(Enum):
    """Enum representing possible invoice statuses."""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        """Return human-readable status."""
        return self.value.capitalize()


@dataclass
class Invoice(BaseModel):
    """Invoice model representing a business invoice."""

    # Basic information
    invoice_number: str = field(default_factory=lambda: f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}")
    customer_id: str = ""
    customer_email: str = ""
    customer_name: str = ""
    issue_date: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    status: InvoiceStatus = InvoiceStatus.DRAFT

    # Financial information
    currency: str = "USD"
    subtotal: float = 0.0
    vat_rate: float = 0.0
    vat_amount: float = 0.0
    discount_percentage: float = 0.0
    discount_amount: float = 0.0
    total: float = 0.0

    # Additional information
    notes: str = ""
    terms: str = ""

    # Items
    items: List[InvoiceItem] = field(default_factory=list)

    # Tracking information
    sent_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    reminder_sent_at: List[datetime] = field(default_factory=list)

    def __post_init__(self):
        """Initialize BaseModel and default values."""
        super().__init__()

        # Set default due date (15 days from issue date)
        if not self.due_date:
            self.due_date = self.issue_date + timedelta(days=15)

    def add_item(self, item: InvoiceItem) -> None:
        """
        Add an item to the invoice.

        Args:
            item: Invoice item to add.
        """
        self.items.append(item)
        self.calculate_totals()
        self.update()

    def remove_item(self, item_id: str) -> bool:
        """
        Remove an item from the invoice.

        Args:
            item_id: ID of the item to remove.

        Returns:
            True if item was removed, False if not found.
        """
        for i, item in enumerate(self.items):
            if item.id == item_id:
                del self.items[i]
                self.calculate_totals()
                self.update()
                return True
        return False

    def calculate_totals(self) -> None:
        """Calculate all financial totals based on items and rates."""
        # Calculate subtotal from items
        self.subtotal = sum(item.total for item in self.items)

        # Calculate discount amount
        if self.discount_percentage > 0:
            self.discount_amount = self.subtotal * (self.discount_percentage / 100)

        # Calculate VAT on the discounted amount
        taxable_amount = self.subtotal - self.discount_amount
        self.vat_amount = taxable_amount * (self.vat_rate / 100)

        # Calculate final total
        self.total = taxable_amount + self.vat_amount

        self.update()

    def send(self) -> None:
        """Mark invoice as sent."""
        if self.status == InvoiceStatus.DRAFT:
            self.status = InvoiceStatus.SENT
            self.sent_at = datetime.now()
            self.update()

    def mark_as_paid(self) -> None:
        """Mark invoice as paid."""
        self.status = InvoiceStatus.PAID
        self.paid_at = datetime.now()
        self.update()

    def cancel(self) -> None:
        """Mark invoice as cancelled."""
        self.status = InvoiceStatus.CANCELLED
        self.update()

    def check_overdue(self) -> bool:
        """
        Check if invoice is overdue.

        Returns:
            True if invoice is overdue, False otherwise.
        """
        if (self.status == InvoiceStatus.SENT and
                self.due_date and self.due_date < datetime.now()):
            self.status = InvoiceStatus.OVERDUE
            self.update()
            return True
        return False

    def record_reminder_sent(self) -> None:
        """Record that a reminder was sent."""
        self.reminder_sent_at.append(datetime.now())
        self.update()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert invoice to a dictionary.

        Returns:
            Dictionary representation of the invoice.
        """
        result = super().to_dict()
        result.update({
            'invoice_number': self.invoice_number,
            'customer_id': self.customer_id,
            'customer_email': self.customer_email,
            'customer_name': self.customer_name,
            'issue_date': self.issue_date.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status.value,

            'currency': self.currency,
            'subtotal': self.subtotal,
            'vat_rate': self.vat_rate,
            'vat_amount': self.vat_amount,
            'discount_percentage': self.discount_percentage,
            'discount_amount': self.discount_amount,
            'total': self.total,

            'notes': self.notes,
            'terms': self.terms,

            'items': [item.to_dict() for item in self.items],

            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'reminder_sent_at': [dt.isoformat() for dt in self.reminder_sent_at]
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Invoice':
        """
        Create an Invoice instance from a dictionary.

        Args:
            data: Dictionary containing invoice data.

        Returns:
            New Invoice instance.
        """
        instance = super().from_dict(cls, data)

        # Set invoice-specific attributes
        instance.invoice_number = data.get('invoice_number', '')
        instance.customer_id = data.get('customer_id', '')
        instance.customer_email = data.get('customer_email', '')
        instance.customer_name = data.get('customer_name', '')

        # Parse dates
        if 'issue_date' in data and isinstance(data['issue_date'], str):
            instance.issue_date = datetime.fromisoformat(data['issue_date'])

        if 'due_date' in data and data['due_date'] and isinstance(data['due_date'], str):
            instance.due_date = datetime.fromisoformat(data['due_date'])

        # Parse status
        if 'status' in data:
            try:
                instance.status = InvoiceStatus(data['status'])
            except ValueError:
                instance.status = InvoiceStatus.DRAFT

        # Set financial information
        instance.currency = data.get('currency', 'USD')
        instance.subtotal = float(data.get('subtotal', 0.0))
        instance.vat_rate = float(data.get('vat_rate', 0.0))
        instance.vat_amount = float(data.get('vat_amount', 0.0))
        instance.discount_percentage = float(data.get('discount_percentage', 0.0))
        instance.discount_amount = float(data.get('discount_amount', 0.0))
        instance.total = float(data.get('total', 0.0))

        # Set additional information
        instance.notes = data.get('notes', '')
        instance.terms = data.get('terms', '')

        # Parse items
        if 'items' in data and isinstance(data['items'], list):
            instance.items = [InvoiceItem.from_dict(item) for item in data['items']]

        # Parse tracking dates
        if 'sent_at' in data and data['sent_at'] and isinstance(data['sent_at'], str):
            instance.sent_at = datetime.fromisoformat(data['sent_at'])

        if 'paid_at' in data and data['paid_at'] and isinstance(data['paid_at'], str):
            instance.paid_at = datetime.fromisoformat(data['paid_at'])

        if 'reminder_sent_at' in data and isinstance(data['reminder_sent_at'], list):
            instance.reminder_sent_at = [
                datetime.fromisoformat(dt) for dt in data['reminder_sent_at']
                if isinstance(dt, str)
            ]

        return instance

    def __str__(self) -> str:
        """Return string representation of invoice."""
        return f"Invoice {self.invoice_number} ({self.status}): {self.currency} {self.total:.2f}"