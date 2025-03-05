"""
User repository module.

This module contains the repository class for user-related data access operations.
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for user-related data access operations.
    """

    def __init__(self, session: Session):
        """Initialize with SQLAlchemy session."""
        super().__init__(session, User)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: Email address to search for

        Returns:
            User instance if found, None otherwise
        """
        return self.session.query(User).filter(
            func.lower(User.email) == func.lower(email)
        ).first()

    def create_user(self, email: str, password: str, **kwargs) -> User:
        """
        Create a new user with proper password hashing.

        Args:
            email: User's email address
            password: User's plaintext password (will be hashed)
            **kwargs: Additional user attributes

        Returns:
            Created user instance
        """
        # Note: The User model will handle password hashing via its setter
        user = self.create(
            email=email,
            password=password,  # This will be hashed in the model
            **kwargs
        )

        return user

    def verify_credentials(self, email: str, password: str) -> Optional[User]:
        """
        Verify user credentials for login.

        Args:
            email: User's email address
            password: User's plaintext password

        Returns:
            User instance if credentials are valid, None otherwise
        """
        user = self.get_by_email(email)

        if user and user.verify_password(password):
            # Update last login timestamp
            user.last_login = datetime.now()
            return user

        return None

    def update_settings(self, user_id: int, settings: Dict[str, Any]) -> Optional[User]:
        """
        Update user settings.

        Args:
            user_id: ID of user to update
            settings: Dictionary of settings to update

        Returns:
            Updated user if successful, None otherwise
        """
        user = self.get_by_id(user_id)
        if user:
            # Merge existing settings with new ones
            current_settings = user.settings or {}
            current_settings.update(settings)
            user.settings = current_settings
            user.updated_at = datetime.now()
            return user
        return None

    def get_setting(self, user_id: int, setting_key: str, default=None) -> Any:
        """
        Get a specific user setting.

        Args:
            user_id: ID of user
            setting_key: Key of setting to retrieve
            default: Default value if setting not found

        Returns:
            Setting value if found, default otherwise
        """
        user = self.get_by_id(user_id)
        if user and user.settings:
            return user.settings.get(setting_key, default)
        return default

    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change user password.

        Args:
            user_id: ID of user
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            Tuple of (success, message)
        """
        user = self.get_by_id(user_id)

        if not user:
            return False, "User not found"

        if not user.verify_password(current_password):
            return False, "Current password is incorrect"

        user.password = new_password
        user.updated_at = datetime.now()

        return True, "Password changed successfully"

    def to_dict(self, user: User, include_private: bool = False) -> Dict[str, Any]:
        """
        Convert user to dictionary representation.

        Args:
            user: User instance to convert
            include_private: Whether to include private fields

        Returns:
            Dictionary representation
        """
        result = {
            'id': user.id,
            'uuid': user.uuid,
            'email': user.email,
            'name': user.name,
            'company_name': user.company_name,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
        }

        if include_private:
            result.update({
                'settings': user.settings,
                'last_login': user.last_login.isoformat() if user.last_login else None
            })

        return result