# /backend/main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path

from .database import engine
from . import models 
from .routers import (
    auth, customers, product, inventory, purchase, 
    sales, crm, service, employee,employee_pages, dashboard, 
    notifications, accounting
)
from .routers import service_api, service_pages

# 1. PATH SETUP
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_FILES_DIR = BASE_DIR / "backend" / "static"
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"

# 2. INITIALIZATION
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Zhagaram Audit", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development; restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. STATIC & TEMPLATES
app.mount("/static", StaticFiles(directory=str(STATIC_FILES_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.include_router(service_api.router)
app.include_router(service_pages.router)

# 4. API ROUTERS
# We use specific prefixes so that the routers can use "/" as their root path
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(product.router, prefix="/api/products", tags=["Products"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(purchase.router, prefix="/api/purchases")
app.include_router(sales.router)
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(crm.router, prefix="/api/crm", tags=["CRM"])
app.include_router(service.router)
app.include_router(employee.router, prefix="/api/employees", tags=["Employees"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(accounting.router)
app.include_router(employee_pages.router)
app.include_router(employee.router)

# 5. UI ROUTES
@app.get("/", include_in_schema=False)
@app.get("/login", include_in_schema=False)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "Login"})

@app.get("/dashboard", include_in_schema=False)
def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "title": "Dashboard"})

@app.get("/products", include_in_schema=False)
def products_page(request: Request):
    return templates.TemplateResponse("products.html", {"request": request, "title": "Products"})

@app.get("/sales", include_in_schema=False)
def sales_page(request: Request):
    return templates.TemplateResponse("sales.html", {"request": request, "title": "Sales"})

@app.get("/sales/new", include_in_schema=False)
def new_sale_page(request: Request):
    return templates.TemplateResponse("new_sale.html", {"request": request, "title": "New Sale"})

@app.get("/sales/{sale_id}", include_in_schema=False)
def sale_detail_page(request: Request, sale_id: int):
    return templates.TemplateResponse("sale_detail.html", {"request": request, "sale_id": sale_id})

@app.get("/customers", include_in_schema=False)
def customers_page(request: Request):
    return templates.TemplateResponse("customers.html", {"request": request, "title": "Customers"})