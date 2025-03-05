"""
Base repository module.

This module contains the abstract base class for all repositories,
defining common methods and patterns for data access operations.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any, Type, Union
from sqlalchemy.orm import Session

from app.models.base import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T], ABC):
    """
    Abstract base repository providing common data access patterns.

    This class should be inherited by concrete repositories that work with
    specific entity types. It provides implementations for common CRUD operations.
    """

    def __init__(self, session: Session, model_class: Type[T]):
        """
        Initialize repository with session and model class.

        Args:
            session: SQLAlchemy database session
            model_class: SQLAlchemy model class this repository will work with
        """
        self.session = session
        self.model_class = model_class

    def create(self, **kwargs) -> T:
        """
        Create a new entity instance.

        Args:
            **kwargs: Entity attributes as keyword arguments

        Returns:
            The created entity instance
        """
        entity = self.model_class(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def get_by_id(self, entity_id: int) -> Optional[T]:
        """
        Get entity by its primary key ID.

        Args:
            entity_id: Primary key ID value

        Returns:
            Entity instance if found, None otherwise
        """
        return self.session.query(self.model_class).get(entity_id)

    def get_by_uuid(self, uuid: str) -> Optional[T]:
        """
        Get entity by its UUID.

        Args:
            uuid: Entity UUID string

        Returns:
            Entity instance if found, None otherwise
        """
        return self.session.query(self.model_class).filter_by(uuid=uuid).first()

    def update(self, entity_id: int, **kwargs) -> Optional[T]:
        """
        Update an existing entity.

        Args:
            entity_id: ID of entity to update
            **kwargs: Entity attributes to update

        Returns:
            Updated entity instance if found, None otherwise
        """
        entity = self.get_by_id(entity_id)
        if entity:
            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            return entity
        return None

    def delete(self, entity_id: int) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_id: ID of entity to delete

        Returns:
            True if entity was deleted, False if not found
        """
        entity = self.get_by_id(entity_id)
        if entity:
            self.session.delete(entity)
            return True
        return False

    def find_all(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """
        Find all entities matching the given filters.

        Args:
            skip: Number of results to skip (for pagination)
            limit: Maximum number of results to return
            **filters: Filter criteria as keyword arguments

        Returns:
            List of entity instances matching criteria
        """
        query = self.session.query(self.model_class)

        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)

        return query.offset(skip).limit(limit).all()

    def count(self, **filters) -> int:
        """
        Count entities matching the given filters.

        Args:
            **filters: Filter criteria as keyword arguments

        Returns:
            Count of matching entities
        """
        query = self.session.query(self.model_class)

        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)

        return query.count()

    @abstractmethod
    def to_dict(self, entity: T) -> Dict[str, Any]:
        """
        Convert entity to dictionary representation.

        Args:
            entity: Entity instance to convert

        Returns:
            Dictionary representation of entity
        """
        pass