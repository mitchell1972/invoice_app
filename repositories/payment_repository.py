"""
Payment repository module.

This module contains the repository class for payment-related data access operations.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session, joinedload

from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.invoice import Invoice
from app.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """
    Repository for payment-related data access operations.
    """

    def __init__(self, session: Session):
        """Initialize with SQLAlchemy session."""
        super().__init__(session, Payment)

    def record_payment(self, invoice_id: int, amount: float,
                       payment_method: PaymentMethod = PaymentMethod.OTHER,
                       payment_date: datetime = None,
                       reference: str = None,
                       notes: str = None) -> Tuple[Payment, Invoice]:
        """
        Record a payment for an invoice.

        Args:
            invoice_id: ID of invoice being paid
            amount: Payment amount
            payment_method: Method of payment
            payment_date: Date of payment (default: now)
            reference: Payment reference/transaction number
            notes: Additional payment notes

        Returns:
            Tuple of (payment, updated_invoice)
        """
        from app.repositories.invoice_repository import InvoiceRepository

        # Create payment record
        payment = self.create(
            invoice_id=invoice_id,
            amount=amount,
            payment_method=payment_method,
            payment_date=payment_date or datetime.now(),
            reference=reference,
            notes=notes,
            status=PaymentStatus.COMPLETED
        )

        # Update invoice status
        invoice_repo = InvoiceRepository(self.session)
        invoice = invoice_repo.mark_as_paid(invoice_id, payment_date)

        return payment, invoice

    def get_payments_for_invoice(self, invoice_id: int) -> List[Payment]:
        """
        Get all payments for an invoice.

        Args:
            invoice_id: ID of invoice

        Returns:
            List of payments for the invoice
        """
        return self.session.query(Payment).filter(
            Payment.invoice_id == invoice_id
        ).order_by(desc(Payment.payment_date)).all()

    def get_recent_payments(self, user_id: int, limit: int = 10) -> List[Payment]:
        """
        Get recent payments for a user.

        Args:
            user_id: ID of user
            limit: Maximum number of payments to return

        Returns:
            List of recent payments
        """
        return self.session.query(Payment).join(
            Invoice, Payment.invoice_id == Invoice.id
        ).filter(
            Invoice.user_id == user_id
        ).order_by(
            desc(Payment.payment_date)
        ).limit(limit).all()

    def get_payment_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get payment statistics for a user.

        Args:
            user_id: ID of user

        Returns:
            Dictionary with payment statistics
        """
        # Total payments by method
        payments_by_method = {}
        for method in PaymentMethod:
            total = self.session.query(func.sum(Payment.amount)).join(
                Invoice, Payment.invoice_id == Invoice.id
            ).filter(
                Invoice.user_id == user_id,
                Payment.payment_method == method,
                Payment.status == PaymentStatus.COMPLETED
            ).scalar() or 0

            payments_by_method[method.value] = total

        # Total payments received
        total_received = self.session.query(func.sum(Payment.amount)).join(
            Invoice, Payment.invoice_id == Invoice.id
        ).filter(
            Invoice.user_id == user_id,
            Payment.status == PaymentStatus.COMPLETED
        ).scalar() or 0

        # Payment count
        payment_count = self.session.query(func.count(Payment.id)).join(
            Invoice, Payment.invoice_id == Invoice.id
        ).filter(
            Invoice.user_id == user_id,
            Payment.status == PaymentStatus.COMPLETED
        ).scalar() or 0

        return {
            'total_received': total_received,
            'payment_count': payment_count,
            'payments_by_method': payments_by_method
        }

    def to_dict(self, payment: Payment) -> Dict[str, Any]:
        """
        Convert payment to dictionary representation.

        Args:
            payment: Payment instance to convert

        Returns:
            Dictionary representation
        """
        return {
            'id': payment.id,
            'uuid': payment.uuid,
            'invoice_id': payment.invoice_id,
            'amount': payment.amount,
            'payment_method': payment.payment_method.value,
            'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
            'reference': payment.reference,
            'notes': payment.notes,
            'status': payment.status.value,
            'created_at': payment.created_at.isoformat() if payment.created_at else None,
            'updated_at': payment.updated_at.isoformat() if payment.updated_at else None,
        }