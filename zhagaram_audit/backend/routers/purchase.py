# /backend/routers/purchase.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from ..database import SessionLocal
from ..models import Supplier as DBSupplier, Purchase, PurchaseItem, InventoryMovement, Expense, Product
from ..audit import log_action
from ..schemas import PurchaseCreate
from sqlalchemy import func 

router = APIRouter(tags=["Purchases"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint: /api/purchases/suppliers (For POST)
@router.post("/suppliers")
def add_supplier(
    name: str,
    contact_person: str = None,
    phone: str = None,
    email: str = None,
    address: str = None,
    db: Session = Depends(get_db)
):
    supplier = DBSupplier(
        name=name,
        contact_person=contact_person,
        phone=phone,
        email=email,
        address=address
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    log_action(1, "CREATE_SUPPLIER", "suppliers", supplier.id)
    return {"message": "Supplier added", "supplier_id": supplier.id}

# Endpoint: /api/purchases/suppliers (For GET)
@router.get("/suppliers")
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(DBSupplier).all()


# -----------------------------------------------------------------
# UPDATE SUPPLIER (PUT)
# -----------------------------------------------------------------
# Endpoint: /api/purchases/suppliers/{supplier_id}
@router.put("/suppliers/{supplier_id}")
def update_supplier(
    supplier_id: int,
    name: str = None,
    contact_person: str = None,
    phone: str = None,
    email: str = None,
    address: str = None,
    db: Session = Depends(get_db)
):
    db_supplier = db.query(DBSupplier).filter(DBSupplier.id == supplier_id).first()

    if not db_supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    if name is not None:
        db_supplier.name = name
    if contact_person is not None:
        db_supplier.contact_person = contact_person
    if phone is not None:
        db_supplier.phone = phone
    if email is not None:
        db_supplier.email = email
    if address is not None:
        db_supplier.address = address

    db.commit()
    db.refresh(db_supplier)
    
    log_action(1, "UPDATE_SUPPLIER", "suppliers", db_supplier.id)
    return {"message": "Supplier updated", "supplier_id": db_supplier.id}


# -----------------------------------------------------------------
# DELETE SUPPLIER (DELETE)
# -----------------------------------------------------------------
# Endpoint: /api/purchases/suppliers/{supplier_id}
@router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    db_supplier = db.query(DBSupplier).filter(DBSupplier.id == supplier_id).first()

    if not db_supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
        
    db.delete(db_supplier)
    db.commit()
    
    log_action(1, "DELETE_SUPPLIER", "suppliers", supplier_id)
    return


# ===============================================
# GET PURCHASE ORDERS LIST (FIXED DATE/TIME)
# ===============================================
# Endpoint: /api/purchases/ (For GET)
@router.get("/")
def list_purchases(db: Session = Depends(get_db)):
    purchases = db.query(Purchase).options(joinedload(Purchase.supplier)).all()
    
    result = []
    for p in purchases:
        supplier_name = p.supplier.name if p.supplier else "N/A"
        result.append({
            "id": p.id,
            "supplier_id": p.supplier_id,
            "supplier_name": supplier_name,
            # FIX: Updated strftime to include time (%H:%M)
            "date": p.created_at.strftime("%Y-%m-%d %H:%M"),
            "total_amount": p.total_amount,
            "status": p.status,
            "action": "View/Receive"
        })
    return result


# ===============================================
# CREATE PURCHASE ORDER
# ===============================================
# Endpoint: /api/purchases/ (For POST)
@router.post("/")
def create_purchase(
    purchase_data: PurchaseCreate,
    db: Session = Depends(get_db)
):
    total_amount = sum(item.quantity * item.unit_price for item in purchase_data.items)
    purchase = Purchase(
        supplier_id=purchase_data.supplier_id,
        total_amount=total_amount,
        remarks=purchase_data.remarks,
        status="PENDING"
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    for item in purchase_data.items:
        purchase_item = PurchaseItem(
            purchase_id=purchase.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price
        )
        db.add(purchase_item)
    db.commit()

    log_action(1, "CREATE_PURCHASE", "purchases", purchase.id)
    return {"message": "Purchase order created", "purchase_id": purchase.id}


# ===============================================
# RECEIVE PURCHASE ORDER (UPDATE STATUS AND INVENTORY)
# ===============================================
# Endpoint: /api/purchases/{purchase_id}/receive
@router.post("/{purchase_id}/receive")
def receive_purchase(purchase_id: int, db: Session = Depends(get_db)):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase Order not found")
        
    if purchase.status == "RECEIVED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Purchase Order already received")

    # Update stock for each item
    items = db.query(PurchaseItem).filter(PurchaseItem.purchase_id == purchase_id).all()
    
    for item in items:
        # 1. Create Inventory Movement
        movement = InventoryMovement(
            product_id=item.product_id,
            movement_type="PURCHASE",
            quantity=item.quantity,
            remarks=f"Stock received via Purchase ID {purchase_id}"
        )
        db.add(movement)
        
        # 2. Update Product Stock Quantity
        db_product = db.query(Product).filter(Product.id == item.product_id).first()
        if db_product:
            db_product.stock_qty += item.quantity
    
    # 3. Update Purchase Order Status
    purchase.status = "RECEIVED"
    db.commit()

    log_action(1, "RECEIVE_PURCHASE", "purchases", purchase.id)
    return {"message": "Stock received and inventory updated successfully"}


# ===============================================
# DELETE PURCHASE ORDER
# ===============================================
# Endpoint: /api/purchases/{purchase_id}
@router.delete("/{purchase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase(purchase_id: int, db: Session = Depends(get_db)):
    db_purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()

    if not db_purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase Order not found")

    if db_purchase.status == "RECEIVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Cannot delete a Purchase Order that has already been received and affected inventory."
        )

    # Delete associated Purchase Items first (due to foreign key constraints)
    db.query(PurchaseItem).filter(PurchaseItem.purchase_id == purchase_id).delete()
    
    # Delete the Purchase Order header
    db.delete(db_purchase)
    db.commit()
    
    log_action(1, "DELETE_PURCHASE", "purchases", purchase_id)
    return


# Endpoint: /api/purchases/expenses
@router.post("/expenses")
def add_expense(description: str, amount: float, purchase_id: int = None, db: Session = Depends(get_db)):
    expense = Expense(
        description=description,
        amount=amount,
        purchase_id=purchase_id
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    log_action(1, "ADD_EXPENSE", "expenses", expense.id)
    return {"message": "Expense recorded", "expense_id": expense.id}