from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Ensures templates are found in the frontend/templates folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))

router = APIRouter(tags=["Employee Pages"])

@router.get("/employees", response_class=HTMLResponse)
def employee_page(request: Request):
    return templates.TemplateResponse(
        "employees.html", 
        {"request": request, "title": "Staff Management"}
    )