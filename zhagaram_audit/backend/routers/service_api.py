from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..database import get_db
from ..models import ServiceTicket, Customer, Product, Employee 

router = APIRouter(
    prefix="/api/service",
    tags=["Service API"]
)

class TicketSchema(BaseModel):
    customer_id: int
    product_id: int
    technician_id: Optional[int] = None
    estimate_parts: Optional[float] = 0.0
    estimate_labor: Optional[float] = 0.0
    remarks: Optional[str] = ""

@router.get("/tickets")
def get_tickets(db: Session = Depends(get_db)):
    # Outer join used so tickets show up even if no technician is assigned
    results = db.query(
        ServiceTicket,
        Customer.name.label("cust_name"),
        Product.model.label("prod_model"),
        Employee.name.label("emp_name")
    ).join(Customer, ServiceTicket.customer_id == Customer.id)\
     .join(Product, ServiceTicket.product_id == Product.id)\
     .outerjoin(Employee, ServiceTicket.technician_id == Employee.id)\
     .all()

    return [{
        "id": t.id,
        "status": t.status or "OPEN",
        "customer_name": cust_name,
        "product_model": prod_model,
        "technician_name": emp_name or "Unassigned",
        "remarks": t.remarks or "",
        "customer_id": t.customer_id,
        "product_id": t.product_id,
        "technician_id": t.technician_id,
        "estimate_parts": float(t.estimate_parts or 0),
        "estimate_labor": float(t.estimate_labor or 0),
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "N/A"
    } for t, cust_name, prod_model, emp_name in results]

@router.post("/tickets")
def create_ticket(ticket: TicketSchema, db: Session = Depends(get_db)):
    # Step 1: Manual Validation (Check if these actually exist in DB)
    if not db.query(Customer).filter(Customer.id == ticket.customer_id).first():
        raise HTTPException(status_code=400, detail=f"Customer ID {ticket.customer_id} not found.")
    
    if not db.query(Product).filter(Product.id == ticket.product_id).first():
        raise HTTPException(status_code=400, detail=f"Product ID {ticket.product_id} not found.")

    if ticket.technician_id:
        if not db.query(Employee).filter(Employee.id == ticket.technician_id).first():
            raise HTTPException(status_code=400, detail=f"Technician ID {ticket.technician_id} not found.")

    # Step 2: Attempt Save with Deep Debugging
    try:
        new_ticket = ServiceTicket(
            customer_id=ticket.customer_id,
            product_id=ticket.product_id,
            technician_id=ticket.technician_id,
            status="OPEN",
            estimate_parts=ticket.estimate_parts or 0.0,
            estimate_labor=ticket.estimate_labor or 0.0,
            remarks=ticket.remarks or "",
            created_at=datetime.now()
        )
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        return new_ticket
    except Exception as e:
        db.rollback()
        # EXTREMELY IMPORTANT: Look at your console terminal when you see this error
        error_msg = str(e)
        print(f"--- DATABASE ERROR START ---")
        print(error_msg)
        print(f"--- DATABASE ERROR END ---")
        raise HTTPException(status_code=500, detail=f"Database Crash: {error_msg}")

@router.put("/tickets/{ticket_id}")
def update_ticket(ticket_id: int, ticket: TicketSchema, status: str, db: Session = Depends(get_db)):
    db_ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    try:
        db_ticket.technician_id = ticket.technician_id
        db_ticket.remarks = ticket.remarks
        db_ticket.status = status
        db_ticket.estimate_parts = ticket.estimate_parts
        db_ticket.estimate_labor = ticket.estimate_labor
        db.commit()
        return {"message": "Updated"}
    except Exception as e:
        db.rollback()
        print(f"Update Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tickets/{ticket_id}")
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    db_ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    try:
        db.delete(db_ticket)
        db.commit()
        return {"message": "Deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))