from pydantic import BaseModel, Field
from typing import List, Optional

# --- AUTH SCHEMAS ---
class LoginData(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- CUSTOMER SCHEMAS ---
class CustomerCreate(BaseModel):
    name: str 
    phone: str
    email: str = "" 
    address: str = ""

# --- PRODUCT SCHEMAS ---
# --- PRODUCT SCHEMAS ---
# Rename ProductBase back to ProductCreate to match your routers
class ProductCreate(BaseModel):
    sku: str
    model: str
    variant: Optional[str] = None
    color: Optional[str] = None
    purchase_price: float
    sale_price: float
    tax_rate: float = 0.0
    stock_qty: int = 0
    low_stock_threshold: int = 5

class Product(ProductCreate):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True

# --- PURCHASE SCHEMAS ---
class PurchaseItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)

class PurchaseCreate(BaseModel):
    supplier_id: int
    items: List[PurchaseItemBase]
    remarks: Optional[str] = None

    class Config:
        from_attributes = True