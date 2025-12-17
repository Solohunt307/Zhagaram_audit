# /backend/routers/crm.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

# FIX: Use double-dot (..) for parent-level imports
from ..database import get_db, SessionLocal # Use SessionLocal for internal get_db function
from ..models import Customer, FollowUp, ServiceTicket, Product
from ..audit import log_action 

router = APIRouter()

# If you don't use this local copy in other functions, you can remove it. 
# We'll use get_db from the database file which is a yield-based dependency.
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# Pydantic Schemas (defined here for clarity, or can be moved to schemas.py)
class FollowUpCreate(BaseModel):
    customer_id: int
    follow_up_date: datetime
    purpose: str 
    notes: Optional[str] = None

class ServiceRecordCreate(BaseModel):
    customer_id: int
    product_id: int
    service_type: str 
    service_date: datetime
    warranty_expiry: Optional[datetime] = None
    remarks: Optional[str] = None


# ---------------------------------------------------------------------
# API Endpoints for Follow-Ups
# ---------------------------------------------------------------------

@router.post("/followups", status_code=status.HTTP_201_CREATED)
def add_followup(
    followup_in: FollowUpCreate,
    db: Session = Depends(get_db)
):
    # 1. Check if Customer exists
    customer = db.query(Customer).filter(Customer.id == followup_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    # 2. Create FollowUp record
    # Note: Ensure FollowUp model in models.py has 'purpose' and 'notes'/'note' fields.
    followup_data = followup_in.model_dump()
    db_followup = FollowUp(**followup_data, status="PENDING") 
    
    db.add(db_followup)
    db.commit()
    db.refresh(db_followup)

    log_action(1, "ADD_FOLLOWUP", "follow_ups", db_followup.id)
    return {"message": "Follow-up scheduled", "followup_id": db_followup.id}

# ... (list_pending_followups and update_followup_status endpoints) ...


# ---------------------------------------------------------------------
# API Endpoints for Service Intake (Basic CRM record)
# ---------------------------------------------------------------------

@router.post("/service_intake", status_code=status.HTTP_201_CREATED)
def intake_service_record(
    service_in: ServiceRecordCreate,
    db: Session = Depends(get_db)
):
    # Check if Customer exists 
    customer = db.query(Customer).filter(Customer.id == service_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    
    # Check if Product exists (optional, but recommended)
    product = db.query(Product).filter(Product.id == service_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    # Create the Service Record (assuming ServiceRecord model exists)
    db_service = ServiceRecord(**service_in.model_dump())
    
    db.add(db_service)
    db.commit()
    db.refresh(db_service)

    log_action(1, "ADD_SERVICE_INTAKE", "service_records", db_service.id)
    return {"message": "Service intake recorded", "record_id": db_service.id}