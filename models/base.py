"""
Base model module providing common functionality for all models.

This module defines the BaseModel class which serves as the foundation
for all models in the application, providing common functionality like
ID generation, timestamps, and serialization.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional


class BaseModel:
    """Base model class with common functionality for all models."""

    def __init__(self, id: Optional[str] = None):
        """
        Initialize a new model instance.

        Args:
            id: Optional ID for the model. If not provided, a UUID is generated.
        """
        self.id = id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def update(self):
        """Update the last modified timestamp."""
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.

        Returns:
            Dictionary representation of the model.
        """
        result = {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """
        Create a model instance from a dictionary.

        Args:
            data: Dictionary containing model data.

        Returns:
            New model instance.
        """
        instance = cls(id=data.get('id'))

        # Parse timestamps if present
        if 'created_at' in data and isinstance(data['created_at'], str):
            instance.created_at = datetime.fromisoformat(data['created_at'])

        if 'updated_at' in data and isinstance(data['updated_at'], str):
            instance.updated_at = datetime.fromisoformat(data['updated_at'])

        return instance