from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
import logging
from pydantic import BaseModel
from ..database import get_db
from ..models import Sale, SaleItem, Product, Payment

# Set up logging to help us catch any database errors
logger = logging.getLogger(__name__)

router = APIRouter(tags=["sales"])

class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int

class SaleCreate(BaseModel):
    customer_id: int
    items: list[SaleItemCreate]
    status: str = "QUOTE"

# --- 1. CREATE SALE (Fixes "Method Not Allowed" & "Not Found") ---
@router.post("/api/sales/", status_code=status.HTTP_201_CREATED)
def create_sale(sale_data: SaleCreate, db: Session = Depends(get_db)):
    try:
        # Generate a unique invoice number
        timestamp = int(datetime.utcnow().timestamp())
        invoice_num = f"INV-{timestamp}"
        
        # Create the main Sale record
        new_sale = Sale(
            customer_id=sale_data.customer_id,
            invoice_number=invoice_num,
            status=sale_data.status,
            total_amount=0,
            paid_amount=0,
            created_at=datetime.utcnow()
        )
        db.add(new_sale)
        db.flush() # Get the new_sale.id before committing

        total_accumulated = 0
        
        # Process items and calculate totals
        for item in sale_data.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            
            # Simple tax calculation logic
            tax_rate = product.tax_rate or 0
            item_total = (item.quantity * product.sale_price) * (1 + tax_rate / 100)
            total_accumulated += item_total
            
            db.add(SaleItem(
                sale_id=new_sale.id,
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.sale_price,
                tax_rate=tax_rate,
                total=item_total
            ))
        
        new_sale.total_amount = total_accumulated
        db.commit()
        return {"id": new_sale.id, "invoice_number": invoice_num, "message": "Sale created successfully"}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sale: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# --- 2. LIST SALES ---
@router.get("/api/sales/")
def list_sales(db: Session = Depends(get_db)):
    sales = db.query(Sale).options(joinedload(Sale.customer)).all()
    return [
        {
            "id": s.id,
            "invoice_number": s.invoice_number or "N/A",
            "customer_name": s.customer.name if s.customer else "Walk-in",
            "date": s.created_at.strftime("%Y-%m-%d") if s.created_at else "N/A",
            "total_amount": float(s.total_amount or 0),
            "status": s.status or "QUOTE"
        } for s in sales
    ]

# --- 3. GET DETAIL ---
@router.get("/api/sales/{sale_id}")
def get_sale_detail(sale_id: int, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(Sale.id == sale_id).options(
        joinedload(Sale.customer), 
        joinedload(Sale.items).joinedload(SaleItem.product),
        joinedload(Sale.payments)
    ).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    return {
        "id": sale.id,
        "invoice_number": sale.invoice_number,
        "customer": {"name": sale.customer.name if sale.customer else "Walk-in"},
        "date": sale.created_at.strftime("%Y-%m-%d"),
        "status": sale.status,
        "total_amount": float(sale.total_amount or 0),
        "paid_amount": float(sale.paid_amount or 0),
        "balance_due": float((sale.total_amount or 0) - (sale.paid_amount or 0)),
        "items": [{"product_name": i.product.model, "quantity": i.quantity, "unit_price": float(i.unit_price), "total": float(i.total or 0)} for i in sale.items],
        "payments": [{"amount": p.amount, "date": p.created_at.strftime("%Y-%m-%d")} for p in sale.payments]
    }

# --- 4. ACTIONS (Payment & Convert) ---
@router.post("/api/sales/{sale_id}/payment")
def add_payment(sale_id: int, amount: float, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale: raise HTTPException(status_code=404)
    db.add(Payment(sale_id=sale_id, amount=amount, payment_type="CASH", created_at=datetime.utcnow()))
    sale.paid_amount = float(sale.paid_amount or 0) + amount
    if sale.paid_amount >= sale.total_amount:
        sale.status = "PAID"
    db.commit()
    return {"message": "Payment recorded"}

@router.post("/api/sales/{sale_id}/convert")
def convert_to_invoice(sale_id: int, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale: raise HTTPException(status_code=404)
    sale.status = "INVOICE"
    db.commit()
    return {"message": "Converted to Invoice"}