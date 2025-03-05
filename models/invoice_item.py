"""
Invoice Item model representing a line item on an invoice.

This module defines the InvoiceItem class which represents an individual
line item on an invoice with its own description, quantity, price, etc.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional

from invoice_app.models.base import BaseModel


@dataclass
class InvoiceItem(BaseModel):
    """Model representing a line item on an invoice."""

    invoice_id: str = ""
    description: str = ""
    quantity: float = 1.0
    unit_price: float = 0.0
    total: float = 0.0

    # Optional fields
    sku: Optional[str] = None
    unit: Optional[str] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None

    def __post_init__(self):
        """Initialize BaseModel and calculate total."""
        super().__init__()
        self.calculate_total()

    def calculate_total(self) -> None:
        """Calculate the total price based on quantity and unit price."""
        self.total = self.quantity * self.unit_price

    def update_quantity(self, quantity: float) -> None:
        """
        Update the quantity and recalculate total.

        Args:
            quantity: New quantity value.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        self.quantity = quantity
        self.calculate_total()
        self.update()

    def update_unit_price(self, unit_price: float) -> None:
        """
        Update the unit price and recalculate total.

        Args:
            unit_price: New unit price value.
        """
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative")

        self.unit_price = unit_price
        self.calculate_total()
        self.update()

    def update_description(self, description: str) -> None:
        """
        Update the description.

        Args:
            description: New description text.
        """
        if not description:
            raise ValueError("Description cannot be empty")

        self.description = description
        self.update()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert invoice item to a dictionary.

        Returns:
            Dictionary representation of the invoice item.
        """
        result = super().to_dict()
        result.update({
            'invoice_id': self.invoice_id,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total': self.total,
            'sku': self.sku,
            'unit': self.unit,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InvoiceItem':
        """
        Create an InvoiceItem instance from a dictionary.

        Args:
            data: Dictionary containing invoice item data.

        Returns:
            New InvoiceItem instance.
        """
        instance = super().from_dict(cls, data)

        # Set invoice item specific attributes
        instance.invoice_id = data.get('invoice_id', '')
        instance.description = data.get('description', '')
        instance.quantity = float(data.get('quantity', 1.0))
        instance.unit_price = float(data.get('unit_price', 0.0))
        instance.total = float(data.get('total', 0.0))
        instance.sku = data.get('sku')
        instance.unit = data.get('unit')

        # Tax information
        if 'tax_rate' in data:
            instance.tax_rate = float(data['tax_rate'])

        if 'tax_amount' in data:
            instance.tax_amount = float(data['tax_amount'])

        # Ensure total is calculated correctly
        if not instance.total or abs(instance.total - (instance.quantity * instance.unit_price)) > 0.01:
            instance.calculate_total()

        return instance

    def __str__(self) -> str:
        """Return string representation of invoice item."""
        return f"{self.description} (x{self.quantity}) @ {self.unit_price:.2f}"