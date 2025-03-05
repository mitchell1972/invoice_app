"""
Customer repository module.

This module contains the repository class for customer-related data access operations.
"""
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload

from app.models.customer import Customer
from app.repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    """
    Repository for customer-related data access operations.
    """

    def __init__(self, session: Session):
        """Initialize with SQLAlchemy session."""
        super().__init__(session, Customer)

    def get_by_email(self, email: str) -> Optional[Customer]:
        """
        Get customer by email address.

        Args:
            email: Email address to search for

        Returns:
            Customer instance if found, None otherwise
        """
        return self.session.query(Customer).filter(
            func.lower(Customer.email) == func.lower(email)
        ).first()

    def find_by_name(self, user_id: int, name_query: str, limit: int = 10) -> List[Customer]:
        """
        Find customers by partial name match.

        Args:
            user_id: ID of user whose customers to search
            name_query: Partial name to search for
            limit: Maximum results to return

        Returns:
            List of matching customers
        """
        search_pattern = f"%{name_query}%"

        return self.session.query(Customer).filter(
            Customer.user_id == user_id,
            Customer.name.ilike(search_pattern)
        ).limit(limit).all()

    def get_customers_with_outstanding_invoices(self, user_id: int) -> List[Tuple[Customer, int, float]]:
        """
        Get customers with outstanding invoices.

        Args:
            user_id: ID of user whose customers to check

        Returns:
            List of tuples (customer, invoice_count, total_outstanding)
        """
        from app.models.invoice import Invoice, InvoiceStatus

        query = self.session.query(
            Customer,
            func.count(Invoice.id).label('invoice_count'),
            func.sum(Invoice.total).label('total_outstanding')
        ).join(
            Invoice, Customer.id == Invoice.customer_id
        ).filter(
            Customer.user_id == user_id,
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.REMINDER_SENT])
        ).group_by(
            Customer.id
        ).having(
            func.count(Invoice.id) > 0
        ).order_by(
            func.sum(Invoice.total).desc()
        )

        return query.all()

    def get_or_create(self, user_id: int, email: str, **kwargs) -> Tuple[Customer, bool]:
        """
        Get existing customer by email or create a new one.

        Args:
            user_id: ID of user who owns the customer
            email: Customer email address
            **kwargs: Additional customer attributes

        Returns:
            Tuple of (customer, created) where created is a boolean
        """
        customer = self.get_by_email(email)

        if customer:
            # Make sure it belongs to this user
            if customer.user_id != user_id:
                # If not, create a new one
                customer = self.create(user_id=user_id, email=email, **kwargs)
                return customer, True

            # Return existing customer
            return customer, False

        # Create new customer
        customer = self.create(user_id=user_id, email=email, **kwargs)
        return customer, True

    def to_dict(self, customer: Customer) -> Dict[str, Any]:
        """
        Convert customer to dictionary representation.

        Args:
            customer: Customer instance to convert

        Returns:
            Dictionary representation
        """
        return {
            'id': customer.id,
            'uuid': customer.uuid,
            'user_id': customer.user_id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'address': customer.address,
            'city': customer.city,
            'state': customer.state,
            'postal_code': customer.postal_code,
            'country': customer.country,
            'notes': customer.notes,
            'created_at': customer.created_at.isoformat() if customer.created_at else None,
            'updated_at': customer.updated_at.isoformat() if customer.updated_at else None,
        }