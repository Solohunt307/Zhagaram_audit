from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ServiceTicket, Customer, Product, Technician

router = APIRouter() # Prefix is handled in main.py

@router.get("/tickets")
def get_tickets(db: Session = Depends(get_db)):
    try:
        # Use outerjoins to prevent 500 errors if a technician is not assigned
        results = db.query(ServiceTicket).all()
        
        ticket_list = []
        for t in results:
            ticket_list.append({
                "id": t.id,
                "status": t.status or "OPEN",
                # Force numeric types to 0 if null to stop JS crashes
                "estimate_parts": float(t.estimate_parts or 0),
                "estimate_labor": float(t.estimate_labor or 0),
                "customer_name": t.customer.name if t.customer else "Unknown",
                "product_model": t.product.model if t.product else "N/A",
                "technician_name": t.technician.name if t.technician else "Unassigned"
            })
        return ticket_list
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Database Error")