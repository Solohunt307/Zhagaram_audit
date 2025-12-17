# /backend/routers/product.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..models import Product as DBProduct
from ..schemas import ProductCreate, Product as ProductSchema

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
def read_products(db: Session = Depends(get_db)):
    products = db.query(DBProduct).all()
    return [
        {
            "id": p.id,
            "sku": p.sku,
            "name": p.model, # Keeps your dropdown working
            "model": p.model,
            "sale_price": float(p.sale_price or 0),
            "tax_rate": float(p.tax_rate or 0),
            "stock_qty": p.stock_qty or 0
        } for p in products
    ]

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    try:
        existing_product = db.query(DBProduct).filter(DBProduct.sku == product_data.sku).first()
        if existing_product:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists.")

        new_product = DBProduct(**product_data.dict())
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{product_id}")
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}")
def update_product(product_id: int, product_data: ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in product_data.dict().items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(DBProduct).filter(DBProduct.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return None