from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from invoice_app.config import get_settings
from invoice_app.db.base import get_db, Base, engine
from invoice_app.models.customer import Customer, CustomerCreate, CustomerUpdate
from invoice_app.models.invoice import Invoice, InvoiceCreate, InvoiceUpdate
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
    try:
        return invoice_crud.create_invoice(db=db, invoice=invoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
def update_invoice(
        invoice_id: str,
        invoice: InvoiceUpdate,
        db: Session = Depends(get_db)
):
    updated_invoice = invoice_crud.update_invoice(db, invoice_id, invoice)
    if not updated_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return updated_invoice

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