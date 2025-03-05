"""
Invoice service for handling invoice-related business operations.

This module defines the InvoiceService class which encapsulates the
business logic for creating, updating, sending, and managing invoices.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from invoice_app.models.invoice import Invoice, InvoiceStatus
from invoice_app.models.invoice_item import InvoiceItem
from invoice_app.models.customer import Customer
from invoice_app.repositories.invoice_repository import InvoiceRepository
from invoice_app.repositories.customer_repository import CustomerRepository
from invoice_app.services.email_service import EmailService
from invoice_app.services.pdf_service import PDFService


logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for handling invoice-related business operations."""

    def __init__(self,
                 invoice_repository: InvoiceRepository,
                 customer_repository: CustomerRepository,
                 email_service: EmailService,
                 pdf_service: PDFService):
        """
        Initialize the invoice service.

        Args:
            invoice_repository: Repository for invoice data.
            customer_repository: Repository for customer data.
            email_service: Service for sending emails.
            pdf_service: Service for generating PDF invoices.
        """
        self.invoice_repository = invoice_repository
        self.customer_repository = customer_repository
        self.email_service = email_service
        self.pdf_service = pdf_service

    def create_invoice(self, customer_id: str, items: List[Dict[str, Any]] = None,
                       **invoice_data) -> Invoice:
        """
        Create a new invoice.

        Args:
            customer_id: ID of the customer for the invoice.
            items: List of invoice items data.
            **invoice_data: Additional invoice data fields.

        Returns:
            Newly created Invoice instance.

        Raises:
            ValueError: If customer not found or validation fails.
        """
        # Get customer
        customer = self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with ID '{customer_id}' not found")

        # Create invoice with customer info
        invoice = Invoice(
            customer_id=customer.id,
            customer_email=customer.email,
            customer_name=customer.name,
            **invoice_data
        )

        # Add items if provided
        if items:
            for item_data in items:
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=item_data.get('description', ''),
                    quantity=float(item_data.get('quantity', 1.0)),
                    unit_price=float(item_data.get('unit_price', 0.0))
                )
                invoice.add_item(item)

        # Calculate totals
        invoice.calculate_totals()

        # Save to repository
        self.invoice_repository.save(invoice)

        logger.info(f"Created invoice {invoice.invoice_number} for {customer.name}")
        return invoice

    def update_invoice(self, invoice_id: str, data: Dict[str, Any]) -> Invoice:
        """
        Update an existing invoice.

        Args:
            invoice_id: ID of the invoice to update.
            data: New data for the invoice.

        Returns:
            Updated Invoice instance.

        Raises:
            ValueError: If invoice not found or cannot be updated.
        """
        # Get invoice
        invoice = self.invoice_repository.get_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice with ID '{invoice_id}' not found")

        # Check if invoice can be updated
        if not invoice.can_be_edited():
            raise ValueError(f"Invoice {invoice.invoice_number} cannot be edited in its current state")

        # Update basic fields
        for key, value in data.items():
            if key != 'items' and hasattr(invoice, key):
                setattr(invoice, key, value)

        # Update items if provided
        if 'items' in data and isinstance(data['items'], list):
            # Clear existing items
            invoice.items = []

            # Add new items
            for item_data in data['items']:
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=item_data.get('description', ''),
                    quantity=float(item_data.get('quantity', 1.0)),
                    unit_price=float(item_data.get('unit_price', 0.0))
                )
                invoice.add_item(item)

        # Recalculate totals
        invoice.calculate_totals()

        # Save to repository
        self.invoice_repository.save(invoice)

        logger.info(f"Updated invoice {invoice.invoice_number}")
        return invoice

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """
        Get an invoice by ID.

        Args:
            invoice_id: ID of the invoice to get.

        Returns:
            Invoice instance if found, None otherwise.
        """
        return self.invoice_repository.get_by_id(invoice_id)

    def list_invoices(self, filters: Dict[str, Any] = None) -> List[Invoice]:
        """
        List invoices, optionally filtered.

        Args:
            filters: Optional filters for the invoices.

        Returns:
            List of matching Invoice instances.
        """
        return self.invoice_repository.list(filters)

    def send_invoice(self, invoice_id: str, subject: str = None,
                     message: str = None) -> bool:
        """
        Send an invoice to the customer by email.

        Args:
            invoice_id: ID of the invoice to send.
            subject: Optional custom email subject.
            message: Optional custom email message.

        Returns:
            True if the invoice was sent successfully, False otherwise.

        Raises:
            ValueError: If invoice not found or cannot be sent.
        """
        # Get invoice
        invoice = self.invoice_repository.get_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice with ID '{invoice_id}' not found")

        # Check if invoice can be sent
        if not invoice.can_be_sent():
            raise ValueError(f"Invoice {invoice.invoice_number} cannot be sent in its current state")

        try:
            # Generate PDF
            pdf_bytes = self.pdf_service.generate_invoice_pdf(invoice)

            # Default subject if not provided
            if not subject:
                subject = f"Invoice {invoice.invoice_number} from Your Business"

            # Default message if not provided
            if not message:
                message = f"""
Dear {invoice.customer_name},

Please find attached invoice {invoice.invoice_number} for {invoice.currency} {invoice.total:.2f}.

Due date: {invoice.due_date.strftime('%Y-%m-%d')}.

Thank you for your business.

Best regards,
Your Business
                """

            # Send email
            email_sent = self.email_service.send_email(
                to_email=invoice.customer_email,
                subject=subject,
                message=message,
                attachments=[
                    {
                        'filename': f"Invoice_{invoice.invoice_number}.pdf",
                        'content': pdf_bytes,
                        'content_type': 'application/pdf'
                    }
                ]
            )

            # Update invoice status if email was sent
            if email_sent:
                invoice.send()
                self.invoice_repository.save(invoice)
                logger.info(f"Invoice {invoice.invoice_number} sent to {invoice.customer_email}")
                return True
            else:
                logger.error(f"Failed to send invoice {invoice.invoice_number} to {invoice.customer_email}")
                return False

        except Exception as e:
            logger.error(f"Error sending invoice {invoice.invoice_number}: {str(e)}")
            return False

    def mark_as_paid(self, invoice_id: str) -> bool:
        """
        Mark an invoice as paid.

        Args:
            invoice_id: ID of the invoice to mark as paid.

        Returns:
            True if the invoice was marked as paid, False otherwise.

        Raises:
            ValueError: If invoice not found.
        """
        # Get invoice
        invoice = self.invoice_repository.get_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice with ID '{invoice_id}' not found")

        try:
            # Mark as paid
            invoice.mark_as_paid()

            # Save to repository
            self.invoice_repository.save(invoice)

            logger.info(f"Invoice {invoice.invoice_number} marked as paid")
            return True

        except Exception as e:
            logger.error(f"Error marking invoice {invoice.invoice_number} as paid: {str(e)}")
            return False

    def check_overdue_invoices(self) -> List[Invoice]:
        """
        Check for invoices that have become overdue.

        Returns:
            List of newly overdue invoices.
        """
        # Get sent invoices
        sent_invoices = self.invoice_repository.list({
            'status': InvoiceStatus.SENT.value
        })

        newly_overdue = []
        for invoice in sent_invoices:
            # Check if overdue
            if invoice.check_overdue():
                # Save updated status
                self.invoice_repository.save(invoice)
                newly_overdue.append(invoice)
                logger.info(f"Invoice {invoice.invoice_number} marked as overdue")

        return newly_overdue

    def generate_invoice_pdf(self, invoice_id: str) -> Optional[bytes]:
        """
        Generate a PDF for an invoice.

        Args:
            invoice_id: ID of the invoice to generate PDF for.

        Returns:
            PDF bytes if generated successfully, None otherwise.

        Raises:
            ValueError: If invoice not found.
        """
        # Get invoice
        invoice = self.invoice_repository.get_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice with ID '{invoice_id}' not found")

        try:
            # Generate PDF
            pdf_bytes = self.pdf_service.generate_invoice_pdf(invoice)
            return pdf_bytes

        except Exception as e:
            logger.error(f"Error generating PDF for invoice {invoice.invoice_number}: {str(e)}")
            return None