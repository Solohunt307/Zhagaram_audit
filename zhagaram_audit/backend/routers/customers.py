# /backend/routers/customers.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
import logging
from pydantic import BaseModel, Field
from typing import Optional
from ..database import get_db
from ..models import Customer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note: Tags are handled in main.py, but keeping it here is fine.
router = APIRouter()

# =================================================================
# PYDANTIC SCHEMAS
# =================================================================
class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    email: Optional[str] = Field(None)
    address: Optional[str] = Field(None)

# -----------------------------------------------------------------
# 1. CREATE Customer (POST) -> Final URL: /api/customers/
# -----------------------------------------------------------------
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_data: CustomerCreate = Body(...),
    db: Session = Depends(get_db)
):
    try:
        # Data preparation
        name_stripped = customer_data.name.strip()
        phone_stripped = customer_data.phone.strip()
        email_stripped = customer_data.email.strip() if customer_data.email else None
        address_stripped = customer_data.address.strip() if customer_data.address else None
        
        # Duplication check
        existing = db.query(Customer).filter(Customer.phone == phone_stripped).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Phone number '{phone_stripped}' already registered."
            )

        db_customer = Customer(
            name=name_stripped,
            phone=phone_stripped,
            email=email_stripped,
            address=address_stripped,
            status="Active"
        )
        
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        return {"message": "Customer created successfully", "id": db_customer.id}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during creation")

# -----------------------------------------------------------------
# 2. GET All Customers -> Final URL: /api/customers/
# -----------------------------------------------------------------
@router.get("/")
def read_customers(db: Session = Depends(get_db)):
    try:
        customers = db.query(Customer).all()
        return customers # FastAPI handles the formatting automatically
    except Exception as e:
        logger.error(f"Error reading customers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve customer list")

# -----------------------------------------------------------------
# 3. UPDATE/DELETE -> Final URL: /api/customers/{id}
# -----------------------------------------------------------------
@router.put("/{customer_id}")
def update_customer(customer_id: int, customer_data: CustomerCreate, db: Session = Depends(get_db)):
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    db_customer.name = customer_data.name.strip()
    db_customer.phone = customer_data.phone.strip()
    db_customer.email = customer_data.email.strip() if customer_data.email else None
    db_customer.address = customer_data.address.strip() if customer_data.address else None

    db.commit()
    return {"message": "Updated successfully"}

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    db.delete(db_customer)
    db.commit()
    return