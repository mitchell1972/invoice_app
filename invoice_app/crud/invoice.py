from typing import List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from invoice_app.models.invoice import (
    InvoiceDB,
    InvoiceItemDB,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceStatus
)

def get_invoice(db: Session, invoice_id: str) -> Optional[InvoiceDB]:
    """Get an invoice by ID."""
    return db.query(InvoiceDB).filter(InvoiceDB.id == invoice_id).first()

def get_invoices(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        customer_id: Optional[str] = None,
        status: Optional[InvoiceStatus] = None
) -> List[InvoiceDB]:
    """Get list of invoices with optional filters."""
    query = db.query(InvoiceDB)

    if customer_id:
        query = query.filter(InvoiceDB.customer_id == customer_id)

    if status:
        query = query.filter(InvoiceDB.status == status)

    return query.order_by(InvoiceDB.created_at.desc()).offset(skip).limit(limit).all()

def create_invoice(db: Session, invoice: InvoiceCreate) -> InvoiceDB:
    """Create new invoice."""
    # Create invoice
    db_invoice = InvoiceDB(
        id=str(uuid4()),
        invoice_number=invoice.invoice_number,
        customer_id=invoice.customer_id,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        status=invoice.status,
        subtotal=invoice.subtotal,
        tax=invoice.tax,
        total=invoice.total,
        notes=invoice.notes,
        recipient_email=invoice.recipient_email,  # Add the new field
        currency_code=invoice.currency_code       # Add the new field
    )
    db.add(db_invoice)
    db.flush()  # Flush to get the ID for invoice items

    # Create invoice items
    for item in invoice.items:
        db_item = InvoiceItemDB(
            id=str(uuid4()),
            invoice_id=db_invoice.id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=item.total
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def update_invoice(
        db: Session,
        invoice_id: str,
        invoice_update: InvoiceUpdate
) -> Optional[InvoiceDB]:
    """Update invoice."""
    db_invoice = get_invoice(db, invoice_id)
    if not db_invoice:
        return None

    # Update invoice fields
    for field, value in invoice_update.model_dump(exclude_unset=True).items():
        setattr(db_invoice, field, value)

    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def delete_invoice(db: Session, invoice_id: str) -> bool:
    """Delete invoice."""
    invoice = get_invoice(db, invoice_id)
    if not invoice:
        return False

    db.delete(invoice)
    db.commit()
    return True

def get_invoice_stats(db: Session) -> dict:
    """Get invoice statistics."""
    total_invoices = db.query(func.count(InvoiceDB.id)).scalar()
    total_revenue = db.query(func.sum(InvoiceDB.total)).filter(
        InvoiceDB.status == InvoiceStatus.PAID
    ).scalar() or 0

    # Get counts by status
    status_counts = (
        db.query(
            InvoiceDB.status,
            func.count(InvoiceDB.id)
        )
        .group_by(InvoiceDB.status)
        .all()
    )

    return {
        "total_invoices": total_invoices,
        "total_revenue": float(total_revenue),
        "status_counts": {
            status: count for status, count in status_counts
        }
    }