from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, event
from contextlib import contextmanager
from typing import Generator
import os

# Get database URL from environment variable with fallback
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/invoice_db"
)

# Create database engine with optimized settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=True  # Enable SQL logging for debugging
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create base class for declarative models
Base = declarative_base()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    with get_db_session() as session:
        yield session

# Database initialization and cleanup functions
def init_db() -> None:
    """Initialize database by creating all tables."""
    Base.metadata.create_all(bind=engine)

def cleanup_db() -> None:
    """Clean up database by dropping all tables."""
    Base.metadata.drop_all(bind=engine)

# Event listener for connection debugging
@event.listens_for(engine, "connect")
def on_connect(dbapi_connection, connection_record):
    """Log when a connection is created."""
    print("Database connection established")

# Import models after Base is defined to avoid circular imports
from invoice_app.models.customer import CustomerDB
from invoice_app.models.invoice import InvoiceDB, InvoiceItemDB