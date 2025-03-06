from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from invoice_app.config import get_settings
from invoice_app.db.base import get_db, Base, engine
from invoice_app.models.customer import Customer, CustomerCreate, CustomerUpdate
from invoice_app.crud import customer as customer_crud

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)