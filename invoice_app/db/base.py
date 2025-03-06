from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, event
from contextlib import contextmanager
from typing import Generator

from invoice_app.config import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Enable connection pool pre-ping
    pool_size=5,  # Set initial pool size
    max_overflow=10  # Set max overflow connections
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for database models
Base = declarative_base()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session with context manager."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    with get_db_session() as session:
        yield session

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas on connection."""
    if settings.DATABASE_URL.startswith('sqlite'):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Import all models here to ensure they are registered with Base.metadata
# This avoids circular import issues
# These imports must be AFTER Base is defined

from invoice_app.models.customer import CustomerDB
from invoice_app.models.invoice import InvoiceDB, InvoiceItemDB