from typing import List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import logging

from invoice_app.models.invoice import (
    InvoiceDB,
    InvoiceItemDB,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceStatus
)

# Set up logger
logger = logging.getLogger(__name__)

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
    try:
        logger.info(f"Creating invoice with number: {invoice.invoice_number}")

        # Create invoice
        db_invoice = InvoiceDB(
            id=str(uuid4()),
            invoice_number=invoice.invoice_number,
            user_id=invoice.user_id,
            customer_id=invoice.customer_id,
            issue_date=invoice.issue_date,
            due_date=invoice.due_date,
            status=invoice.status,
            subtotal=invoice.subtotal,
            tax=invoice.tax,
            total=invoice.total,
            notes=invoice.notes,
            recipient_email=invoice.recipient_email,
            currency_code=invoice.currency_code
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
        logger.info(f"Invoice created successfully: {db_invoice.id}")
        return db_invoice
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating invoice: {str(e)}")
        raise

def update_invoice(
        db: Session,
        invoice_id: str,
        invoice_update: InvoiceUpdate
) -> Optional[InvoiceDB]:
    """Update invoice with full support for all fields including items."""
    try:
        logger.info(f"Updating invoice {invoice_id}")
        logger.debug(f"Update data: {invoice_update.model_dump(exclude_unset=True)}")

        db_invoice = get_invoice(db, invoice_id)
        if not db_invoice:
            logger.warning(f"Invoice {invoice_id} not found")
            return None

        # Get update data excluding items
        update_data = invoice_update.model_dump(exclude_unset=True)
        items_data = update_data.pop('items', None)

        logger.debug(f"Updating invoice fields: {update_data}")

        # Update invoice fields
        for field, value in update_data.items():
            # Skip None values to allow partial updates
            if value is not None:
                setattr(db_invoice, field, value)

        # Update items if provided
        if items_data is not None:
            logger.debug(f"Updating items: {items_data}")

            # Delete existing items
            db.query(InvoiceItemDB).filter(InvoiceItemDB.invoice_id == invoice_id).delete()

            # Create new items
            for item in items_data:
                db_item = InvoiceItemDB(
                    id=str(uuid4()),
                    invoice_id=invoice_id,
                    description=item.get('description', '') or 'Unnamed item',
                    quantity=float(item.get('quantity', 1)),
                    unit_price=float(item.get('unit_price', 0)),
                    total=float(item.get('total', 0))
                )
                db.add(db_item)

        try:
            db.commit()
            db.refresh(db_invoice)
            logger.info(f"Invoice {invoice_id} updated successfully")
            return db_invoice
        except Exception as e:
            db.rollback()
            logger.error(f"Database error updating invoice {invoice_id}: {str(e)}")
            raise
    except Exception as e:
        logger.error(f"Error updating invoice {invoice_id}: {str(e)}")
        if 'db' in locals():
            db.rollback()
        raise

def delete_invoice(db: Session, invoice_id: str) -> bool:
    """Delete invoice."""
    try:
        invoice = get_invoice(db, invoice_id)
        if not invoice:
            return False

        db.delete(invoice)
        db.commit()
        logger.info(f"Invoice {invoice_id} deleted successfully")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting invoice {invoice_id}: {str(e)}")
        raise

def get_invoice_stats(db: Session) -> dict:
    """Get invoice statistics."""
    try:
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
    except Exception as e:
        logger.error(f"Error getting invoice stats: {str(e)}")
        raise