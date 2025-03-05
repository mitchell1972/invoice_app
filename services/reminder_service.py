"""
Reminder service for handling invoice payment reminders.

This module defines the ReminderService class which manages
the scheduling and sending of payment reminders for overdue invoices.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from invoice_app.models.invoice import Invoice, InvoiceStatus
from invoice_app.models.reminder import ReminderSettings
from invoice_app.repositories.invoice_repository import InvoiceRepository
from invoice_app.repositories.reminder_repository import ReminderRepository
from invoice_app.services.email_service import EmailService
from invoice_app.services.pdf_service import PDFService


logger = logging.getLogger(__name__)


class ReminderService:
    """Service for handling invoice payment reminders."""

    def __init__(self,
                 invoice_repository: InvoiceRepository,
                 reminder_repository: ReminderRepository,
                 email_service: EmailService,
                 pdf_service: PDFService):
        """
        Initialize the reminder service.

        Args:
            invoice_repository: Repository for invoice data.
            reminder_repository: Repository for reminder settings.
            email_service: Service for sending emails.
            pdf_service: Service for generating PDF invoices.
        """
        self.invoice_repository = invoice_repository
        self.reminder_repository = reminder_repository
        self.email_service = email_service
        self.pdf_service = pdf_service

    def get_settings(self, owner_id: str) -> ReminderSettings:
        """
        Get reminder settings for an owner.

        Args:
            owner_id: ID of the settings owner.

        Returns:
            ReminderSettings instance.
        """
        # Try to get existing settings
        settings = self.reminder_repository.get_by_owner_id(owner_id)

        # Create new settings if none exist
        if not settings:
            settings = ReminderSettings(owner_id=owner_id)
            self.reminder_repository.save(settings)

        return settings

    def update_settings(self, owner_id: str, data: Dict[str, Any]) -> ReminderSettings:
        """
        Update reminder settings.

        Args:
            owner_id: ID of the settings owner.
            data: New settings data.

        Returns:
            Updated ReminderSettings instance.
        """
        # Get current settings
        settings = self.get_settings(owner_id)

        # Update fields
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        # Save updated settings
        self.reminder_repository.save(settings)

        logger.info(f"Updated reminder settings for owner {owner_id}")
        return settings

    def process_reminders(self, owner_id: str) -> Dict[str, Any]:
        """
        Process and send reminders for overdue invoices.

        Args:
            owner_id: ID of the owner to process reminders for.

        Returns:
            Dictionary with results (invoices processed, reminders sent, errors).
        """
        # Get settings
        settings = self.get_settings(owner_id)

        # Skip if reminders are disabled
        if not settings.enabled:
            logger.info(f"Reminders are disabled for owner {owner_id}")
            return {
                'processed': 0,
                'sent': 0,
                'errors': 0,
                'skipped': 0,
                'disabled': True
            }

        # Get overdue invoices
        overdue_invoices = self.invoice_repository.list({
            'status': InvoiceStatus.OVERDUE.value
        })

        # Track results
        results = {
            'processed': len(overdue_invoices),
            'sent': 0,
            'errors': 0,
            'skipped': 0,
            'disabled': False
        }

        # Process each invoice
        for invoice in overdue_invoices:
            try:
                # Calculate days overdue
                days_overdue = (datetime.now() - invoice.due_date).days

                # Get which reminder to send (1-based)
                reminder_number = self._get_reminder_number(settings, invoice)

                if reminder_number:
                    # Send reminder
                    sent = self._send_reminder(invoice, reminder_number, days_overdue, settings)

                    if sent:
                        # Record that reminder was sent
                        invoice.record_reminder_sent()
                        self.invoice_repository.save(invoice)

                        results['sent'] += 1
                        logger.info(f"Sent reminder #{reminder_number} for invoice {invoice.invoice_number}")
                    else:
                        results['errors'] += 1
                        logger.error(f"Failed to send reminder for invoice {invoice.invoice_number}")
                else:
                    # No reminder due yet
                    results['skipped'] += 1
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Error processing reminder for invoice {invoice.invoice_number}: {str(e)}")

        # Update last run timestamp
        settings.update_last_run()
        self.reminder_repository.save(settings)

        return results

    def _get_reminder_number(self, settings: ReminderSettings, invoice: Invoice) -> Optional[int]:
        """
        Determine which reminder number to send for an invoice.

        Args:
            settings: Reminder settings.
            invoice: Invoice to check.

        Returns:
            Reminder number (1-based) to send, or None if no reminder should be sent.
        """
        # Don't send reminders for non-overdue invoices
        if invoice.status != InvoiceStatus.OVERDUE:
            return None

        # Calculate days overdue
        days_overdue = (datetime.now() - invoice.due_date).days

        # Get how many reminders have already been sent
        reminders_sent = len(invoice.reminder_sent_at)

        # Check if we've already sent all configured reminders
        if reminders_sent >= len(settings.reminder_days):
            return None

        # Get the day threshold for the next reminder
        next_threshold = settings.reminder_days[reminders_sent] if reminders_sent < len(settings.reminder_days) else None

        # If no more thresholds, or not enough days overdue yet, don't send
        if next_threshold is None or days_overdue < next_threshold:
            return None

        # Return the 1-based reminder number
        return reminders_sent + 1

    def _send_reminder(self, invoice: Invoice, reminder_number: int,
                       days_overdue: int, settings: ReminderSettings) -> bool:
        """
        Send a reminder email for an invoice.

        Args:
            invoice: Invoice to send reminder for.
            reminder_number: Which reminder in the sequence (1-based).
            days_overdue: Number of days the invoice is overdue.
            settings: Reminder settings.

        Returns:
            True if reminder was sent successfully, False otherwise.
        """
        try:
            # Get reminder template
            subject_template, message_template = settings.get_reminder_template(reminder_number)

            # Format template variables
            template_vars = {
                'invoice_number': invoice.invoice_number,
                'customer_name': invoice.customer_name,
                'issue_date': invoice.issue_date.strftime('%Y-%m-%d'),
                'due_date': invoice.due_date.strftime('%Y-%m-%d'),
                'days_overdue': days_overdue,
                'currency': invoice.currency,
                'total': f"{invoice.total:.2f}",
                'reminder_number': reminder_number
            }

            # Format subject and message
            subject = subject_template.format(**template_vars)
            message = message_template.format(**template_vars)

            # Generate PDF
            pdf_bytes = self.pdf_service.generate_invoice_pdf(invoice)

            # Send email
            return self.email_service.send_email(
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
        except Exception as e:
            logger.error(f"Error sending reminder for invoice {invoice.invoice_number}: {str(e)}")
            return False