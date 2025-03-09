from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
from invoice_app.config import get_settings
from invoice_app.db.base import get_db, Base, engine
from invoice_app.models.customer import Customer, CustomerCreate, CustomerUpdate
from invoice_app.models.invoice import Invoice, InvoiceCreate, InvoiceUpdate, InvoiceItem, InvoiceStatus
from invoice_app.crud import customer as customer_crud
from invoice_app.crud import invoice as invoice_crud

# Create database tables
Base.metadata.create_all(bind=engine)

settings = get_settings()
app = FastAPI(title=settings.PROJECT_NAME)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Invoice App API"}

# Customer endpoints
@app.post("/api/v1/customers/", response_model=Customer)
def create_customer(
        customer: CustomerCreate,
        db: Session = Depends(get_db)
):
    try:
        return customer_crud.create_customer(db=db, customer=customer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/customers/", response_model=List[Customer])
def list_customers(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    return customer_crud.get_customers(db, skip=skip, limit=limit)

@app.get("/api/v1/customers/{customer_id}", response_model=Customer)
def get_customer(
        customer_id: str,
        db: Session = Depends(get_db)
):
    customer = customer_crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.put("/api/v1/customers/{customer_id}", response_model=Customer)
def update_customer(
        customer_id: str,
        customer: CustomerUpdate,
        db: Session = Depends(get_db)
):
    try:
        updated_customer = customer_crud.update_customer(
            db, customer_id, customer
        )
        if not updated_customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return updated_customer
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/v1/customers/{customer_id}")
def delete_customer(
        customer_id: str,
        db: Session = Depends(get_db)
):
    if not customer_crud.delete_customer(db, customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted successfully"}

# Invoice endpoints
@app.post("/api/v1/invoices/", response_model=Invoice)
def create_invoice(
        invoice: InvoiceCreate,
        db: Session = Depends(get_db)
):
    # Log the invoice data for debugging
    print("Received invoice data:", invoice.model_dump())
    print("Items:", invoice.items)

    try:
        return invoice_crud.create_invoice(db=db, invoice=invoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Add more detailed error information
        print(f"Error creating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/api/v1/invoices/", response_model=List[Invoice])
def list_invoices(
        skip: int = 0,
        limit: int = 100,
        customer_id: str = None,
        db: Session = Depends(get_db)
):
    return invoice_crud.get_invoices(db, skip=skip, limit=limit, customer_id=customer_id)

@app.get("/api/v1/invoices/{invoice_id}", response_model=Invoice)
def get_invoice(
        invoice_id: str,
        db: Session = Depends(get_db)
):
    invoice = invoice_crud.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@app.put("/api/v1/invoices/{invoice_id}", response_model=Invoice)
async def update_invoice(
        invoice_id: str,
        invoice: InvoiceUpdate,
        db: Session = Depends(get_db)
):
    try:
        print(f"Received update for invoice {invoice_id}: {invoice.model_dump(exclude_unset=True)}")
        updated_invoice = invoice_crud.update_invoice(db, invoice_id, invoice)
        if not updated_invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return updated_invoice
    except Exception as e:
        print(f"Error updating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating invoice: {str(e)}")

# New endpoint to handle form submissions from the web interface
@app.post("/api/v1/invoices/{invoice_id}/form-update")
async def update_invoice_form(
        invoice_id: str,
        request: Request,
        db: Session = Depends(get_db)
):
    try:
        # Parse form data
        form_data = await request.form()

        # Convert to dict for easier access
        data = dict(form_data)
        print(f"Received form data for invoice {invoice_id}: {data}")

        # Extract invoice fields from form data
        invoice_number = data.get("invoice_number")
        recipient_email = data.get("recipient_email")
        issue_date = datetime.strptime(data.get("issue_date", ""), "%Y-%m-%d") if data.get("issue_date") else None
        due_date = datetime.strptime(data.get("due_date", ""), "%Y-%m-%d") if data.get("due_date") else None
        status = data.get("status")
        currency_code = data.get("currency_code", "USD")
        notes = data.get("notes", "")

        # Process invoice items
        items = []
        i = 0
        while f"item_description_{i}" in data:
            item = {
                "description": data.get(f"item_description_{i}", ""),
                "quantity": float(data.get(f"item_quantity_{i}", 0)),
                "unit_price": float(data.get(f"item_unit_price_{i}", 0)),
                "total": float(data.get(f"item_total_{i}", 0))
            }
            items.append(item)
            i += 1

        # Calculate financial values
        subtotal = float(data.get("subtotal", 0))
        tax = float(data.get("tax", 0))
        total = float(data.get("total", 0))

        # Create update object
        update_data = InvoiceUpdate(
            invoice_number=invoice_number,
            recipient_email=recipient_email,
            issue_date=issue_date,
            due_date=due_date,
            status=status,
            currency_code=currency_code,
            notes=notes,
            subtotal=subtotal,
            tax=tax,
            total=total,
            items=items
        )

        # Update invoice in database
        updated_invoice = invoice_crud.update_invoice(db, invoice_id, update_data)
        if not updated_invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Redirect back to invoice page
        return {"message": "Invoice updated successfully", "invoice_id": invoice_id}

    except Exception as e:
        print(f"Error updating invoice form: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating invoice: {str(e)}")

@app.delete("/api/v1/invoices/{invoice_id}")
def delete_invoice(
        invoice_id: str,
        db: Session = Depends(get_db)
):
    if not invoice_crud.delete_invoice(db, invoice_id):
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"message": "Invoice deleted successfully"}

@app.get("/api/v1/invoices/stats/", response_model=dict)
def get_invoice_stats(db: Session = Depends(get_db)):
    return invoice_crud.get_invoice_stats(db)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)