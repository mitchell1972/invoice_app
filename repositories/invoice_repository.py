"""
Invoice repository module.

This module contains the repository class for invoice-related data access operations.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Union

from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session, joinedload

from app.models.invoice import Invoice, InvoiceStatus
from app.models.customer import Customer
from app.repositories.base_repository import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    """
    Repository for invoice-related data access operations.
    """

    def __init__(self, session: Session):
        """Initialize with SQLAlchemy session."""
        super().__init__(session, Invoice)

    def create_invoice(self, user_id: int, customer_id: int, amount: float,
                       vat_rate: float, discount: float = 0,
                       status: InvoiceStatus = InvoiceStatus.DRAFT,
                       **kwargs) -> Invoice:
        """
        Create a new invoice with proper calculations.

        Args:
            user_id: ID of user creating the invoice
            customer_id: ID of customer for this invoice
            amount: Base amount before VAT
            vat_rate: VAT rate as percentage (e.g. 20 for 20%)
            discount: Discount amount (if any)
            status: Initial invoice status (default: DRAFT)
            **kwargs: Additional invoice attributes

        Returns:
            Created invoice instance
        """
        # Generate a unique invoice number
        invoice_number = self._generate_invoice_number()

        # Calculate financial fields
        subtotal = amount
        vat_amount = (subtotal - discount) * (vat_rate / 100)
        total = subtotal - discount + vat_amount

        # Create the invoice
        invoice = self.create(
            invoice_number=invoice_number,
            user_id=user_id,
            customer_id=customer_id,
            subtotal=subtotal,
            discount=discount,
            vat_rate=vat_rate,
            vat_amount=vat_amount,
            total=total,
            status=status,
            **kwargs
        )

        return invoice

    def _generate_invoice_number(self) -> str:
        """
        Generate a unique invoice number.

        Returns:
            Unique invoice number string
        """
        # Get current date and year
        now = datetime.now()
        year = now.year

        # Find the highest invoice number for this year
        prefix = f"INV-{year}-"
        highest_invoice = self.session.query(Invoice).filter(
            Invoice.invoice_number.like(f"{prefix}%")
        ).order_by(desc(Invoice.invoice_number)).first()

        if highest_invoice:
            # Extract the sequence number and increment
            try:
                seq_number = int(highest_invoice.invoice_number.split('-')[-1])
                next_number = seq_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1

        # Format with leading zeros (e.g., INV-2023-0001)
        return f"{prefix}{next_number:04d}"

    def mark_as_sent(self, invoice_id: int, sent_date: datetime = None) -> Optional[Invoice]:
        """
        Mark an invoice as sent.

        Args:
            invoice_id: ID of invoice to update
            sent_date: Date when sent (default: current time)

        Returns:
            Updated invoice if successful, None otherwise
        """
        invoice = self.get_by_id(invoice_id)
        if invoice and invoice.status == InvoiceStatus.DRAFT:
            invoice.status = InvoiceStatus.SENT
            invoice.sent_date = sent_date or datetime.now()
            invoice.updated_at = datetime.now()
            return invoice
        return None

    def mark_as_paid(self, invoice_id: int, payment_date: datetime = None) -> Optional[Invoice]:
        """
        Mark an invoice as paid.

        Args:
            invoice_id: ID of invoice to update
            payment_date: Date when paid (default: current time)

        Returns:
            Updated invoice if successful, None otherwise
        """
        invoice = self.get_by_id(invoice_id)
        if invoice and invoice.status in [InvoiceStatus.SENT, InvoiceStatus.REMINDER_SENT]:
            invoice.status = InvoiceStatus.PAID
            invoice.payment_date = payment_date or datetime.now()
            invoice.updated_at = datetime.now()
            return invoice
        return None

    def find_invoices_for_reminder(self, days_threshold: int) -> List[Invoice]:
        """
        Find invoices that need reminders.

        This finds sent invoices that are unpaid and haven't received a reminder
        within the specified threshold days.

        Args:
            days_threshold: Days after which to send a reminder

        Returns:
            List of invoices needing reminders
        """
        reminder_date = datetime.now() - timedelta(days=days_threshold)

        query = self.session.query(Invoice).filter(
            # Only consider sent invoices
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.REMINDER_SENT]),

            # That don't have a recent reminder
            or_(
                Invoice.last_reminder_date.is_(None),
                Invoice.last_reminder_date < reminder_date
            ),

            # And were sent before the threshold
            Invoice.sent_date < reminder_date
        )

        return query.all()

    def record_reminder_sent(self, invoice_id: int) -> Optional[Invoice]:
        """
        Record that a reminder was sent for an invoice.

        Args:
            invoice_id: ID of invoice that received a reminder

        Returns:
            Updated invoice if successful, None otherwise
        """
        invoice = self.get_by_id(invoice_id)
        if invoice and invoice.status in [InvoiceStatus.SENT, InvoiceStatus.REMINDER_SENT]:
            invoice.status = InvoiceStatus.REMINDER_SENT
            invoice.last_reminder_date = datetime.now()
            invoice.reminder_count = (invoice.reminder_count or 0) + 1
            invoice.updated_at = datetime.now()
            return invoice
        return None

    def get_invoice_with_customer(self, invoice_id: int) -> Optional[Invoice]:
        """
        Get invoice with customer data preloaded.

        Args:
            invoice_id: ID of invoice to fetch

        Returns:
            Invoice with customer relationship loaded
        """
        return self.session.query(Invoice).options(
            joinedload(Invoice.customer)
        ).filter(
            Invoice.id == invoice_id
        ).first()

    def get_invoices_by_status(self, user_id: int, status: InvoiceStatus,
                               skip: int = 0, limit: int = 100) -> List[Invoice]:
        """
        Get invoices by status for a specific user.

        Args:
            user_id: ID of user to get invoices for
            status: Status to filter by
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of invoices matching criteria
        """
        query = self.session.query(Invoice).filter(
            Invoice.user_id == user_id,
            Invoice.status == status
        ).order_by(desc(Invoice.created_at))

        return query.offset(skip).limit(limit).all()

    def get_invoice_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get invoice statistics for a user.

        Args:
            user_id: ID of user to get statistics for

        Returns:
            Dictionary with statistics
        """
        # Count by status
        status_counts = {}
        for status in InvoiceStatus:
            count = self.session.query(func.count(Invoice.id)).filter(
                Invoice.user_id == user_id,
                Invoice.status == status
            ).scalar()
            status_counts[status.value] = count

        # Total amounts
        total_invoiced = self.session.query(func.sum(Invoice.total)).filter(
            Invoice.user_id == user_id
        ).scalar() or 0

        total_paid = self.session.query(func.sum(Invoice.total)).filter(
            Invoice.user_id == user_id,
            Invoice.status == InvoiceStatus.PAID
        ).scalar() or 0

        total_outstanding = self.session.query(func.sum(Invoice.total)).filter(
            Invoice.user_id == user_id,
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.REMINDER_SENT])
        ).scalar() or 0

        return {
            'status_counts': status_counts,
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'total_outstanding': total_outstanding
        }

    def to_dict(self, invoice: Invoice) -> Dict[str, Any]:
        """
        Convert invoice to dictionary representation.

        Args:
            invoice: Invoice instance to convert

        Returns:
            Dictionary representation
        """
        return {
            'id': invoice.id,
            'uuid': invoice.uuid,
            'invoice_number': invoice.invoice_number,
            'user_id': invoice.user_id,
            'customer_id': invoice.customer_id,
            'subtotal': invoice.subtotal,
            'discount': invoice.discount,
            'vat_rate': invoice.vat_rate,
            'vat_amount': invoice.vat_amount,
            'total': invoice.total,
            'status': invoice.status.value,
            'created_at': invoice.created_at.isoformat() if invoice.created_at else None,
            'updated_at': invoice.updated_at.isoformat() if invoice.updated_at else None,
            'sent_date': invoice.sent_date.isoformat() if invoice.sent_date else None,
            'payment_date': invoice.payment_date.isoformat() if invoice.payment_date else None,
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'last_reminder_date': invoice.last_reminder_date.isoformat() if invoice.last_reminder_date else None,
            'reminder_count': invoice.reminder_count or 0,
        }