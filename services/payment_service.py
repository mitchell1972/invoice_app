"""
Payment service module.

This module contains the service class for payment-related business logic.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.repositories.payment_repository import PaymentRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.services.email_service import EmailService


class PaymentService:
    """
    Service for payment-related business logic.

    This class orchestrates operations involving payments, including
    recording payments, generating receipts, and handling refunds.
    """

    def __init__(self,
                 session: Session,
                 payment_repository: Optional[PaymentRepository] = None,
                 invoice_repository: Optional[InvoiceRepository] = None,
                 email_service: Optional[EmailService] = None):
        """
        Initialize the service with repositories.

        Args:
            session: SQLAlchemy database session
            payment_repository: Repository for payment operations (optional)
            invoice_repository: Repository for invoice operations (optional)
            email_service: Service for sending emails (optional)
        """
        self.session = session
        self.payment_repo = payment_repository or PaymentRepository(session)
        self.invoice_repo = invoice_repository or InvoiceRepository(session)
        self.email_service = email_service or EmailService()

    def record_payment(self, invoice_id: int, amount: float,
                       payment_method: PaymentMethod = PaymentMethod.OTHER,
                       payment_date: datetime = None,
                       reference: str = None,
                       notes: str = None,
                       send_receipt: bool = True) -> Tuple[Payment, Invoice]:
        """
        Record a payment for an invoice and perform related actions.

        This method records the payment, updates the invoice status,
        and optionally sends a receipt email to the customer.

        Args:
            invoice_id: ID of invoice being paid
            amount: Payment amount
            payment_method: Method of payment
            payment_date: Date of payment (default: now)
            reference: Payment reference/transaction number
            notes: Additional payment notes
            send_receipt: Whether to send receipt email

        Returns:
            Tuple of (payment, updated_invoice)

        Raises:
            ValueError: If payment validation fails
        """
        # Get the invoice to validate it exists and has remaining balance
        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice with ID {invoice_id} not found")

        # Validate payment amount
        if amount <= 0:
            raise ValueError("Payment amount must be positive")

        # Check if this would overpay the invoice
        if amount > invoice.total - invoice.amount_paid:
            # Handle potential overpayment (could implement business logic here)
            # For now, just log a warning but allow it
            print(f"Warning: Payment amount {amount} exceeds remaining balance "
                  f"{invoice.total - invoice.amount_paid} for invoice {invoice_id}")

        # Start a transaction
        try:
            # Record the payment
            payment, updated_invoice = self.payment_repo.record_payment(
                invoice_id=invoice_id,
                amount=amount,
                payment_method=payment_method,
                payment_date=payment_date,
                reference=reference,
                notes=notes
            )

            # Send receipt email if requested
            if send_receipt and updated_invoice.status == InvoiceStatus.PAID:
                self._send_payment_receipt(payment, updated_invoice)

            # Commit the transaction
            self.session.commit()

            return payment, updated_invoice

        except Exception as e:
            # Rollback in case of error
            self.session.rollback()
            raise

    def process_refund(self, payment_id: int, refund_amount: Optional[float] = None,
                       refund_reason: str = "", send_notification: bool = True) -> Tuple[Payment, Invoice]:
        """
        Process a refund for a payment.

        Args:
            payment_id: ID of payment to refund
            refund_amount: Amount to refund (default: full payment amount)
            refund_reason: Reason for the refund
            send_notification: Whether to send notification email

        Returns:
            Tuple of (refund_payment, updated_invoice)

        Raises:
            ValueError: If refund validation fails
        """
        # Get the original payment
        original_payment = self.payment_repo.get_by_id(payment_id)
        if not original_payment:
            raise ValueError(f"Payment with ID {payment_id} not found")

        # Validate refund is possible
        if original_payment.status != PaymentStatus.COMPLETED:
            raise ValueError(f"Cannot refund payment with status {original_payment.status.value}")

        # Set refund amount if not specified
        if refund_amount is None:
            refund_amount = original_payment.amount

        # Validate refund amount
        if refund_amount <= 0 or refund_amount > original_payment.amount:
            raise ValueError(f"Invalid refund amount: {refund_amount}")

        # Get the invoice
        invoice = self.invoice_repo.get_by_id(original_payment.invoice_id)
        if not invoice:
            raise ValueError(f"Invoice for payment {payment_id} not found")

        try:
            # Create a refund payment (negative amount)
            refund_payment = self.payment_repo.create(
                invoice_id=original_payment.invoice_id,
                amount=-refund_amount,  # Negative amount for refund
                payment_method=original_payment.payment_method,
                payment_date=datetime.now(),
                reference=f"REFUND-{original_payment.reference}" if original_payment.reference else None,
                notes=f"Refund for payment {payment_id}. Reason: {refund_reason}",
                status=PaymentStatus.COMPLETED,
                is_refund=True,
                refund_reason=refund_reason
            )

            # Update original payment status if full refund
            if refund_amount >= original_payment.amount:
                original_payment.status = PaymentStatus.REFUNDED

            # Update invoice
            invoice.amount_paid -= refund_amount

            # Update invoice status if needed
            if invoice.amount_paid < invoice.total:
                if invoice.amount_paid > 0:
                    invoice.status = InvoiceStatus.PARTIALLY_PAID
                else:
                    invoice.status = InvoiceStatus.SENT

            # Send notification if requested
            if send_notification:
                self._send_refund_notification(refund_payment, invoice)

            # Commit changes
            self.session.commit()

            return refund_payment, invoice

        except Exception as e:
            self.session.rollback()
            raise

    def get_payment_history(self, invoice_id: int) -> List[Dict[str, Any]]:
        """
        Get payment history for an invoice.

        Args:
            invoice_id: ID of invoice

        Returns:
            List of payments as dictionaries
        """
        payments = self.payment_repo.get_payments_for_invoice(invoice_id)
        return [self.payment_repo.to_dict(payment) for payment in payments]

    def generate_payment_receipt(self, payment_id: int) -> Dict[str, Any]:
        """
        Generate a receipt for a payment.

        Args:
            payment_id: ID of payment

        Returns:
            Dictionary with receipt data

        Raises:
            ValueError: If payment not found
        """
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise ValueError(f"Payment with ID {payment_id} not found")

        invoice = self.invoice_repo.get_by_id(payment.invoice_id)
        if not invoice:
            raise ValueError(f"Invoice for payment {payment_id} not found")

        # Get customer information
        customer = invoice.customer

        # Build receipt data
        receipt = {
            'receipt_number': f"RCP-{payment.id}",
            'receipt_date': datetime.now().isoformat(),
            'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
            'payment_method': payment.payment_method_display,
            'reference': payment.reference,
            'amount': payment.amount,
            'formatted_amount': payment.formatted_amount,
            'invoice_number': invoice.invoice_number,
            'customer': {
                'name': customer.name if customer else "Unknown",
                'email': customer.email if customer else None,
            },
            'company': {
                'name': invoice.user.company_name if invoice.user else "Your Company",
                'email': invoice.user.email if invoice.user else None,
            }
        }

        return receipt

    def _send_payment_receipt(self, payment: Payment, invoice: Invoice) -> bool:
        """
        Send payment receipt email.

        Args:
            payment: Payment that was made
            invoice: Updated invoice

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.email_service:
            return False

        # Get customer email
        recipient = invoice.customer.email if invoice.customer else None
        if not recipient:
            return False

        # Generate receipt data
        receipt = self.generate_payment_receipt(payment.id)

        # Prepare email
        subject = f"Payment Receipt for Invoice {invoice.invoice_number}"

        # Send the email
        return self.email_service.send_payment_receipt(
            recipient=recipient,
            subject=subject,
            receipt_data=receipt
        )

    def _send_refund_notification(self, refund: Payment, invoice: Invoice) -> bool:
        """
        Send refund notification email.

        Args:
            refund: Refund payment
            invoice: Updated invoice

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.email_service:
            return False

        # Get customer email
        recipient = invoice.customer.email if invoice.customer else None
        if not recipient:
            return False

        # Prepare email
        subject = f"Refund Processed for Invoice {invoice.invoice_number}"

        # Send the email
        return self.email_service.send_refund_notification(
            recipient=recipient,
            subject=subject,
            refund_amount=abs(refund.amount),
            invoice_number=invoice.invoice_number,
            refund_reason=refund.refund_reason or "No reason provided"
        )