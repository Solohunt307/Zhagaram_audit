# /backend/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, timezone

# =================================================================
# CORE & AUTH MODELS
# =================================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False) # Must be 'password'
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    action = Column(String(255))
    table_name = Column(String(100))
    record_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

# =================================================================
# CRM & CUSTOMER MODELS
# =================================================================
class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    status = Column(String(50), default="Active", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    sales = relationship("Sale", back_populates="customer")
    service_tickets = relationship("ServiceTicket", back_populates="customer")

class FollowUp(Base):
    __tablename__ = "follow_ups"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    followup_date = Column(DateTime)
    note = Column(String(255))
    status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, server_default=func.now())

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    type = Column(String(50))
    message = Column(String(255))
    sent_at = Column(DateTime, server_default=func.now())
    status = Column(String(50), default="PENDING")

# =================================================================
# SALES & BILLING MODELS
# =================================================================
class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    invoice_number = Column(String(50), unique=True, nullable=False)
    status = Column(String(50), default="QUOTE")
    paid_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    payment_type = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", back_populates="sales")
    payments = relationship("Payment", back_populates="sale")
    items = relationship("SaleItem", back_populates="sale")

class SaleItem(Base):
    __tablename__ = "sale_items"
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    unit_price = Column(Float)
    tax_rate = Column(Float)
    total = Column(Float)
    
    product = relationship("Product", back_populates="sale_items")
    sale = relationship("Sale", back_populates="items")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    amount = Column(Float)
    payment_type = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    sale = relationship("Sale", back_populates="payments")

# =================================================================
# INVENTORY & PURCHASE MODELS
# =================================================================
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True, nullable=False)
    model = Column(String(100), nullable=False)
    variant = Column(String(100), nullable=True)  # New field from your screenshot
    color = Column(String(50), nullable=True)      # New field from your screenshot
    purchase_price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=False)
    tax_rate = Column(Float, default=0.0)         # New field from your screenshot
    stock_qty = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5) # New field from your screenshot
    is_active = Column(Boolean, default=True)
    
    # Relationships
    service_tickets = relationship("ServiceTicket", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")
    purchase_items = relationship("PurchaseItem", back_populates="product")

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    movement_type = Column(String(50))
    quantity = Column(Integer)
    serial_number = Column(String(100), nullable=True)
    remarks = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(50))
    address = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    purchases = relationship("Purchase", back_populates="supplier")

class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    total_amount = Column(Float, default=0)
    status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, server_default=func.now())
    
    supplier = relationship("Supplier", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase")

class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    id = Column(Integer, primary_key=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    unit_price = Column(Float)
    
    purchase = relationship("Purchase", back_populates="items")
    product = relationship("Product", back_populates="purchase_items")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    description = Column(String(255))
    amount = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

# =================================================================
# SERVICE & TECHNICIAN MODELS
# =================================================================
class Technician(Base):
    __tablename__ = "technicians"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    service_tickets = relationship("ServiceTicket", back_populates="technician")

class ServiceTicket(Base):
    __tablename__ = "service_tickets"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    status = Column(String(50), default="RECEIVED")
    estimate_parts = Column(Float, default=0.0)
    estimate_labor = Column(Float, default=0.0)
    remarks = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    customer = relationship("Customer", back_populates="service_tickets")
    product = relationship("Product", back_populates="service_tickets")
    technician = relationship("Technician", back_populates="service_tickets")
    service_parts = relationship("ServicePart", back_populates="ticket")

class ServicePart(Base):
    __tablename__ = "service_parts"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("service_tickets.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    unit_price = Column(Float)
    ticket = relationship("ServiceTicket", back_populates="service_parts")

# =================================================================
# HR & EMPLOYEE MODELS
# =================================================================
class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(50)) # e.g., 'Technician', 'Admin', 'Sales'
    phone = Column(String(20))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    # Using lambda ensure the time is captured at the moment of insertion
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    title = Column(String(100), nullable=False)
    description = Column(String(255))
    status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, server_default=func.now())

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    activity = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    check_in = Column(DateTime)
    check_out = Column(DateTime, nullable=True)