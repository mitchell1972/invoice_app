"""
Email service for sending emails.

This module defines the EmailService class which handles
sending emails, including invoices and payment reminders.
"""
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Dict, Any, Optional

from invoice_app.config.settings import get_settings


logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    def __init__(self, config=None):
        """
        Initialize the email service.

        Args:
            config: Optional email configuration. If not provided,
                   will be loaded from application settings.
        """
        # Load configuration
        self.config = config or get_settings().get('email', {})

        # Validate required configuration
        self._validate_config()

    def _validate_config(self) -> None:
        """
        Validate email configuration.

        Raises:
            ValueError: If required configuration is missing.
        """
        required_fields = ['smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email']
        missing_fields = [field for field in required_fields if field not in self.config]

        if missing_fields:
            raise ValueError(f"Missing required email configuration: {', '.join(missing_fields)}")

    def send_email(self, to_email: str, subject: str, message: str,
                   cc: List[str] = None, bcc: List[str] = None,
                   attachments: List[Dict[str, Any]] = None) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address.
            subject: Email subject.
            message: Email body text.
            cc: Optional list of CC recipients.
            bcc: Optional list of BCC recipients.
            attachments: Optional list of attachments. Each attachment is a dict
                        with 'filename', 'content', and 'content_type' keys.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add CC and BCC if provided
            if cc:
                msg['Cc'] = ', '.join(cc)

            if bcc:
                msg['Bcc'] = ', '.join(bcc)

            # Add message body
            msg.attach(MIMEText(message, 'plain'))

            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    if all(k in attachment for k in ['filename', 'content', 'content_type']):
                        part = MIMEApplication(attachment['content'])
                        part.add_header('Content-Disposition', 'attachment',
                                        filename=attachment['filename'])
                        msg.attach(part)

            # Build recipient list
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Connect to SMTP server and send email
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                # Secure the connection
                context = ssl.create_default_context()
                server.starttls(context=context)

                # Login
                server.login(self.config['smtp_username'], self.config['smtp_password'])

                # Send email
                server.sendmail(self.config['from_email'], recipients, msg.as_string())

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False

    def send_test_email(self, to_email: str) -> bool:
        """
        Send a test email to verify configuration.

        Args:
            to_email: Recipient email address.

        Returns:
            True if test email was sent successfully, False otherwise.
        """
        subject = "Test Email from Invoice App"
        message = """
This is a test email from your Invoice App.

If you're receiving this, your email configuration is working correctly.

Best regards,
Invoice App
        """

        return self.send_email(to_email, subject, message)