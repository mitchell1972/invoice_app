"""
Reminder model for invoice payment reminders.

This module defines the ReminderSettings class which controls
the automated sending of payment reminders for overdue invoices.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from invoice_app.models.base import BaseModel


@dataclass
class ReminderSettings(BaseModel):
    """Model for configuring invoice payment reminders."""

    # Owner ID (usually user or business ID)
    owner_id: str = ""

    # Whether automatic reminders are enabled
    enabled: bool = True

    # Days after due date when reminders should be sent
    reminder_days: List[int] = field(default_factory=lambda: [3, 7, 14])

    # Custom reminder subject lines (keyed by reminder number, 1-based)
    subjects: Dict[int, str] = field(default_factory=dict)

    # Custom reminder message templates (keyed by reminder number, 1-based)
    templates: Dict[int, str] = field(default_factory=dict)

    # Reminder history
    last_run: Optional[datetime] = None

    def __post_init__(self):
        """Initialize BaseModel and default values."""
        super().__init__()

        # Set default templates if empty
        if not self.subjects:
            self.subjects = {
                1: "Payment Reminder: Invoice {invoice_number} is due soon",
                2: "Second Reminder: Invoice {invoice_number} is overdue",
                3: "FINAL NOTICE: Invoice {invoice_number} requires immediate payment"
            }

        if not self.templates:
            self.templates = {
                1: """
Dear {customer_name},

This is a friendly reminder that payment for Invoice {invoice_number} 
is now {days_overdue} days overdue. 

Invoice details:
- Invoice number: {invoice_number}
- Issue date: {issue_date}
- Due date: {due_date}
- Amount due: {currency} {total}

Please make payment at your earliest convenience.

Thank you for your business.
                """,

                2: """
Dear {customer_name},

We noticed that Invoice {invoice_number} remains unpaid and is now 
{days_overdue} days overdue.

Invoice details:
- Invoice number: {invoice_number}
- Issue date: {issue_date}
- Due date: {due_date}
- Amount due: {currency} {total}

Please make payment as soon as possible or contact us if you have any questions.

Thank you for your prompt attention to this matter.
                """,

                3: """
Dear {customer_name},

FINAL NOTICE: Invoice {invoice_number} is now {days_overdue} days overdue
and requires immediate attention.

Invoice details:
- Invoice number: {invoice_number}
- Issue date: {issue_date}
- Due date: {due_date}
- Amount due: {currency} {total}

Please make payment immediately to avoid any potential late fees or
further action.

If you have already made the payment, please disregard this notice.
                """
            }

    def get_next_reminder_day(self, days_overdue: int) -> Optional[int]:
        """
        Get the next reminder day based on how many days the invoice is overdue.

        Args:
            days_overdue: Number of days the invoice is overdue.

        Returns:
            Next reminder day threshold, or None if no more reminders.
        """
        # Sort reminder days to ensure they're in ascending order
        sorted_days = sorted(self.reminder_days)

        # Find the next reminder day threshold
        for day in sorted_days:
            if days_overdue <= day:
                return day

        return None

    def get_reminder_template(self, reminder_number: int) -> tuple:
        """
        Get the subject and template for a specific reminder number.

        Args:
            reminder_number: Which reminder in the sequence (1-based).

        Returns:
            Tuple of (subject, template) for the reminder.
        """
        # Default templates in case the requested one doesn't exist
        default_subject = "Payment Reminder: Your invoice is overdue"
        default_template = "Please pay your overdue invoice {invoice_number} as soon as possible."

        # Get subject and template
        subject = self.subjects.get(reminder_number, default_subject)
        template = self.templates.get(reminder_number, default_template)

        return subject, template

    def update_last_run(self) -> None:
        """Update the last run timestamp to now."""
        self.last_run = datetime.now()
        self.update()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert reminder settings to a dictionary.

        Returns:
            Dictionary representation of the reminder settings.
        """
        result = super().to_dict()
        result.update({
            'owner_id': self.owner_id,
            'enabled': self.enabled,
            'reminder_days': self.reminder_days,
            'subjects': self.subjects,
            'templates': self.templates,
            'last_run': self.last_run.isoformat() if self.last_run else None
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReminderSettings':
        """
        Create a ReminderSettings instance from a dictionary.

        Args:
            data: Dictionary containing reminder settings data.

        Returns:
            New ReminderSettings instance.
        """
        instance = super().from_dict(cls, data)

        # Set reminder-specific attributes
        instance.owner_id = data.get('owner_id', '')
        instance.enabled = data.get('enabled', True)

        # Parse reminder days
        if 'reminder_days' in data and isinstance(data['reminder_days'], list):
            instance.reminder_days = [int(day) for day in data['reminder_days']]

        # Parse templates dictionaries
        if 'subjects' in data and isinstance(data['subjects'], dict):
            instance.subjects = {int(k): v for k, v in data['subjects'].items()}

        if 'templates' in data and isinstance(data['templates'], dict):
            instance.templates = {int(k): v for k, v in data['templates'].items()}

        # Parse last run timestamp
        if 'last_run' in data and data['last_run'] and isinstance(data['last_run'], str):
            instance.last_run = datetime.fromisoformat(data['last_run'])

        return instance

    def __str__(self) -> str:
        """Return string representation of reminder settings."""
        status = "Enabled" if self.enabled else "Disabled"
        days = ", ".join(str(day) for day in sorted(self.reminder_days))
        return f"Reminder Settings ({status}): Days [{days}]"