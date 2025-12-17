from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db # Use the common get_db from your database file
from ..models import Sale, SaleItem, Product, ServiceTicket, InventoryMovement
# Remove log_action if it's causing issues, or ensure audit.py exists
try:
    from ..audit import log_action
except ImportError:
    def log_action(*args): pass 

from datetime import date

router = APIRouter()

@router.get("/kpi/daily")
def daily_kpi(db: Session = Depends(get_db)):
    today = date.today()
    
    # 1. Total Sales for today
    sales_total = db.query(func.sum(Sale.total_amount)).filter(func.date(Sale.created_at) == today).scalar() or 0
    
    # 2. Total Cost for today's items to calculate profit
    cost_total = db.query(
        func.sum(SaleItem.quantity * Product.purchase_price)
    ).join(Product, SaleItem.product_id == Product.id)\
     .join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(func.date(Sale.created_at) == today).scalar() or 0
    
    gross_profit = float(sales_total) - float(cost_total)

    log_action(1, "VIEW_DAILY_KPI", "dashboard", 0)
    
    # Matches the keys expected by dashboard.html: sales_total and gross_profit
    return {
        "date": str(today), 
        "sales_total": float(sales_total), 
        "gross_profit": gross_profit
    }

@router.get("/kpi/top_products")
def top_products(db: Session = Depends(get_db)):
    top = db.query(
        Product.id, Product.model, func.sum(SaleItem.quantity).label("sold_qty")
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .group_by(Product.id)\
     .order_by(func.sum(SaleItem.quantity).desc())\
     .limit(5).all()

    log_action(1, "VIEW_TOP_PRODUCTS", "dashboard", 0)
    return {"top_products": [{"product_id": p.id, "model": p.model, "sold_qty": p.sold_qty} for p in top]}

@router.get("/kpi/outstanding_services")
def outstanding_services(db: Session = Depends(get_db)):
    tickets = db.query(ServiceTicket).filter(ServiceTicket.status != "DELIVERED").all()
    log_action(1, "VIEW_OUTSTANDING_SERVICES", "dashboard", 0)
    return {"outstanding_services": [{"ticket_id": t.id, "status": t.status} for t in tickets]}

@router.get("/kpi/stock_valuation")
def stock_valuation(db: Session = Depends(get_db)):
    # Calculate current stock by model
    stock = db.query(
        Product.id, Product.model, Product.purchase_price, Product.stock_qty
    ).all()

    valuation = sum([p.purchase_price * p.stock_qty for p in stock])
    log_action(1, "VIEW_STOCK_VALUATION", "dashboard", 0)
    return {
        "total_stock_valuation": valuation, 
        "stock_details": [{"product_id": p.id, "model": p.model, "qty": p.stock_qty, "value": p.purchase_price * p.stock_qty} for p in stock]
    }