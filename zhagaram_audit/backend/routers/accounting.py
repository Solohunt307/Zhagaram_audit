from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
import csv
import os

from ..database import get_db
from ..models import Sale, SaleItem, Purchase, Customer
from ..audit import log_action

router = APIRouter(
    prefix="/api/accounting",
    tags=["Accounting"]
)

# 1. Provide JSON data for the HTML Table
@router.get("/ledger/data")
def get_ledger_data(db: Session = Depends(get_db)):
    try:
        sales = db.query(Sale).order_by(Sale.created_at.desc()).all()
        return [{
            "id": s.id,
            "invoice": s.invoice_number,
            "total": float(s.total_amount or 0),
            "gst": float(s.gst_total or 0),
            "paid": float(s.paid_amount or 0),
            "balance": float((s.total_amount or 0) - (s.paid_amount or 0)),
            "status": s.status,
            "date": s.created_at.strftime("%Y-%m-%d") if s.created_at else "N/A"
        } for s in sales]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data Fetch Error: {str(e)}")

# 2. Export logic (Original logic with fixed paths)
@router.get("/ledger/sales/export")
def export_sales_ledger(db: Session = Depends(get_db)):
    try:
        sales = db.query(Sale).all()
        filename = f"sales_ledger_{date.today()}.csv"
        # Saves in the project root
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Invoice No", "Total", "GST", "Paid", "Status", "Date"])
            for s in sales:
                writer.writerow([s.invoice_number, s.total_amount, s.gst_total, s.paid_amount, s.status, s.created_at])
        
        return {"message": "Exported successfully", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))