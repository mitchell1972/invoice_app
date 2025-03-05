"""
Reminder repository module.

This module contains the repository class for reminder-related data access operations.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session, joinedload

from app.models.reminder import Reminder, ReminderStatus
from app.models.invoice import Invoice
from app.repositories.base_repository import BaseRepository


class ReminderRepository(BaseRepository[Reminder]):
    """
    Repository for reminder-related data access operations.
    """

    def __init__(self, session: Session):
        """Initialize with SQLAlchemy session."""
        super().__init__(session, Reminder)

    def create_reminder(self, invoice_id: int, scheduled_date: datetime,
                        template_id: Optional[int] = None,
                        custom_message: Optional[str] = None) -> Reminder:
        """
        Create a new payment reminder.

        Args:
            invoice_id: ID of invoice for the reminder
            scheduled_date: Date when reminder should be sent
            template_id: ID of reminder template to use (optional)
            custom_message: Custom reminder message (optional)

        Returns:
            Created reminder instance
        """
        # Get invoice to verify it exists
        invoice = self.session.query(Invoice).get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice with ID {invoice_id} not found")

        reminder = self.create(
            invoice_id=invoice_id,
            user_id=invoice.user_id,
            customer_id=invoice.customer_id,
            template_id=template_id,
            custom_message=custom_message,
            scheduled_date=scheduled_date,
            status=ReminderStatus.SCHEDULED
        )

        return reminder

    def get_due_reminders(self) -> List[Reminder]:
        """
        Get reminders that are due to be sent.

        Returns:
            List of reminders that should be sent now
        """
        now = datetime.now()

        return self.session.query(Reminder).filter(
            Reminder.status == ReminderStatus.SCHEDULED,
            Reminder.scheduled_date <= now
        ).order_by(
            Reminder.scheduled_date
        ).all()

    def mark_as_sent(self, reminder_id: int, sent_date: datetime = None) -> Optional[Reminder]:
        """
        Mark a reminder as sent.

        Args:
            reminder_id: ID of reminder
            sent_date: Date when reminder was sent (default: now)

        Returns:
            Updated reminder if successful, None otherwise
        """
        reminder = self.get_by_id(reminder_id)
        if reminder and reminder.status == ReminderStatus.SCHEDULED:
            reminder.status = ReminderStatus.SENT
            reminder.sent_date = sent_date or datetime.now()
            reminder.updated_at = datetime.now()

            # Update the invoice's last reminder date
            from app.repositories.invoice_repository import InvoiceRepository
            invoice_repo = InvoiceRepository(self.session)
            invoice_repo.record_reminder_sent(reminder.invoice_id)

            return reminder
        return None

    def mark_as_failed(self, reminder_id: int, error_message: str) -> Optional[Reminder]:
        """
        Mark a reminder as failed.

        Args:
            reminder_id: ID of reminder
            error_message: Error message explaining the failure

        Returns:
            Updated reminder if successful, None otherwise
        """
        reminder = self.get_by_id(reminder_id)
        if reminder and reminder.status == ReminderStatus.SCHEDULED:
            reminder.status = ReminderStatus.FAILED
            reminder.error_message = error_message
            reminder.updated_at = datetime.now()
            return reminder
        return None

    def get_reminders_for_invoice(self, invoice_id: int) -> List[Reminder]:
        """
        Get all reminders for an invoice.

        Args:
            invoice_id: ID of invoice

        Returns:
            List of reminders for the invoice
        """
        return self.session.query(Reminder).filter(
            Reminder.invoice_id == invoice_id
        ).order_by(desc(Reminder.scheduled_date)).all()

    def get_reminder_with_details(self, reminder_id: int) -> Optional[Reminder]:
        """
        Get a reminder with invoice and customer details loaded.

        Args:
            reminder_id: ID of reminder to fetch

        Returns:
            Reminder with relationships loaded
        """
        return self.session.query(Reminder).options(
            joinedload(Reminder.invoice),
            joinedload(Reminder.customer)
        ).filter(
            Reminder.id == reminder_id
        ).first()

    def schedule_automatic_reminders(self, invoice_id: int,
                                     reminder_days: List[int],
                                     template_id: Optional[int] = None) -> List[Reminder]:
        """
        Schedule automatic reminders for an invoice.

        Args:
            invoice_id: ID of invoice
            reminder_days: List of days after due date for reminders
            template_id: ID of reminder template to use

        Returns:
            List of created reminders
        """
        invoice = self.session.query(Invoice).get(invoice_id)
        if not invoice or not invoice.due_date:
            raise ValueError("Invoice not found or missing due date")

        reminders = []
        for days in reminder_days:
            scheduled_date = invoice.due_date + datetime.timedelta(days=days)

            # Don't schedule reminders in the past
            if scheduled_date < datetime.now():
                continue

            reminder = self.create_reminder(
                invoice_id=invoice_id,
                scheduled_date=scheduled_date,
                template_id=template_id
            )
            reminders.append(reminder)

        return reminders

    def to_dict(self, reminder: Reminder) -> Dict[str, Any]:
        """
        Convert reminder to dictionary representation.

        Args:
            reminder: Reminder instance to convert

        Returns:
            Dictionary representation
        """
        return {
            'id': reminder.id,
            'uuid': reminder.uuid,
            'invoice_id': reminder.invoice_id,
            'user_id': reminder.user_id,
            'customer_id': reminder.customer_id,
            'template_id': reminder.template_id,
            'custom_message': reminder.custom_message,
            'scheduled_date': reminder.scheduled_date.isoformat() if reminder.scheduled_date else None,
            'sent_date': reminder.sent_date.isoformat() if reminder.sent_date else None,
            'status': reminder.status.value,
            'error_message': reminder.error_message,
            'created_at': reminder.created_at.isoformat() if reminder.created_at else None,
            'updated_at': reminder.updated_at.isoformat() if reminder.updated_at else None,
        }