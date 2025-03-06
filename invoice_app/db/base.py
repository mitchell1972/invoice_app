from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, event
from contextlib import contextmanager
from typing import Generator
import os

# Database URL from environment or default
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/invoice_db"
)

# Create database engine with connection pooling
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Enable connection ping
    pool_size=5,         # Set initial pool size
    max_overflow=10      # Allow up to 10 connections beyond pool_size
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

# Add event listeners for debugging (optional)
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    print("Database connection established")

@event.listens_for(engine, "disconnect")
def disconnect(dbapi_connection, connection_record):
    print("Database connection closed")

# Import models to ensure they are registered with the metadata
# This must be after Base is defined
from invoice_app.models.customer import CustomerDB
from invoice_app.models.invoice import InvoiceDB, InvoiceItemDB

# Create all tables
def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)

def cleanup_db():
    """Cleanup database by dropping all tables."""
    Base.metadata.drop_all(bind=engine) 