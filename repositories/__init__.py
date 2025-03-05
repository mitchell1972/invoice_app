"""
Repositories package.

This package contains repository classes that handle data access operations
for the application. Each repository follows the repository pattern to abstract
database operations from business logic.
"""
from typing import Dict, Type, Any
from sqlalchemy.orm import Session

from app.repositories.base_repository import BaseRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.user_repository import UserRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.reminder_repository import ReminderRepository

# Dictionary mapping model names to repository classes
REPOSITORY_MAP = {
    'invoice': InvoiceRepository,
    'customer': CustomerRepository,
    'user': UserRepository,
    'payment': PaymentRepository,
    'reminder': ReminderRepository,
}


class RepositoryFactory:
    """
    Factory class to create repositories.

    This class helps create repository instances with dependency injection
    of the database session.
    """

    def __init__(self, session: Session):
        """
        Initialize the factory with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self._repositories: Dict[str, BaseRepository] = {}

    def get_repository(self, repository_name: str) -> BaseRepository:
        """
        Get a repository instance by name.

        Args:
            repository_name: Name of repository to get

        Returns:
            Repository instance

        Raises:
            ValueError: If repository name is not recognized
        """
        if repository_name not in REPOSITORY_MAP:
            raise ValueError(f"Unknown repository: {repository_name}")

        # Create repository if not already cached
        if repository_name not in self._repositories:
            repository_class = REPOSITORY_MAP[repository_name]
            self._repositories[repository_name] = repository_class(self.session)

        return self._repositories[repository_name]

    @property
    def invoice(self) -> InvoiceRepository:
        """Get the invoice repository."""
        return self.get_repository('invoice')

    @property
    def customer(self) -> CustomerRepository:
        """Get the customer repository."""
        return self.get_repository('customer')

    @property
    def user(self) -> UserRepository:
        """Get the user repository."""
        return self.get_repository('user')

    @property
    def payment(self) -> PaymentRepository:
        """Get the payment repository."""
        return self.get_repository('payment')

    @property
    def reminder(self) -> ReminderRepository:
        """Get the reminder repository."""
        return self.get_repository('reminder')