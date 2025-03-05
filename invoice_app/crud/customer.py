from typing import List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from invoice_app.models.customer import CustomerDB, CustomerCreate, CustomerUpdate

def get_customer(db: Session, customer_id: str) -> Optional[CustomerDB]:
    """Get a customer by ID."""
    return db.query(CustomerDB).filter(CustomerDB.id == customer_id).first()

def get_customer_by_email(db: Session, email: str) -> Optional[CustomerDB]:
    """Get a customer by email."""
    return db.query(CustomerDB).filter(CustomerDB.email == email).first()

def get_customers(
    db: Session, skip: int = 0, limit: int = 100
) -> List[CustomerDB]:
    """Get list of customers."""
    return db.query(CustomerDB).offset(skip).limit(limit).all()

def create_customer(db: Session, customer: CustomerCreate) -> CustomerDB:
    """Create new customer."""
    db_customer = CustomerDB(
        id=str(uuid4()),
        **customer.model_dump()
    )
    try:
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        return db_customer
    except IntegrityError:
        db.rollback()
        raise ValueError("Customer with this email already exists")

def update_customer(
    db: Session, customer_id: str, customer: CustomerUpdate
) -> Optional[CustomerDB]:
    """Update customer."""
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return None
        
    update_data = customer.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_customer, field, value)

    try:
        db.commit()
        db.refresh(db_customer)
        return db_customer
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already registered")

def delete_customer(db: Session, customer_id: str) -> bool:
    """Delete customer."""
    customer = get_customer(db, customer_id)
    if not customer:
        return False
    
    db.delete(customer)
    db.commit()
    return True 