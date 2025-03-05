"""
Customer model representing a business client.

This module defines the Customer class which stores information about
customers that receive invoices.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import re

from invoice_app.models.base import BaseModel


@dataclass
class Customer(BaseModel):
    """Customer model representing a business client."""

    name: str = ""
    email: str = ""
    company: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """Initialize BaseModel and validate fields."""
        super().__init__()

    def validate(self) -> bool:
        """
        Validate customer data.

        Returns:
            True if the customer data is valid, False otherwise.

        Raises:
            ValueError: If validation fails.
        """
        # Validate required fields
        if not self.name:
            raise ValueError("Customer name is required")

        # Validate email
        if not self.email:
            raise ValueError("Customer email is required")

        # Simple email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email):
            raise ValueError("Invalid email format")

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert customer to a dictionary.

        Returns:
            Dictionary representation of the customer.
        """
        result = super().to_dict()
        result.update({
            'name': self.name,
            'email': self.email,
            'company': self.company,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'notes': self.notes
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Customer':
        """
        Create a Customer instance from a dictionary.

        Args:
            data: Dictionary containing customer data.

        Returns:
            New Customer instance.
        """
        instance = super().from_dict(cls, data)

        # Set customer-specific attributes
        instance.name = data.get('name', '')
        instance.email = data.get('email', '')
        instance.company = data.get('company')
        instance.phone = data.get('phone')
        instance.address = data.get('address')
        instance.city = data.get('city')
        instance.state = data.get('state')
        instance.postal_code = data.get('postal_code')
        instance.country = data.get('country')
        instance.notes = data.get('notes')

        return instance

    def __str__(self) -> str:
        """Return string representation of customer."""
        return f"{self.name} <{self.email}>"