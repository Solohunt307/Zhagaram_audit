import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

# This ensures we find the 'frontend/templates' folder regardless of how you start the server
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["Service Pages"])

@router.get("/service", response_class=HTMLResponse)
def service_list(request: Request):
    # We verify the file exists before trying to render it to prevent a 500 error
    if not os.path.exists(TEMPLATES_DIR / "service.html"):
        return HTMLResponse(content=f"Error: service.html not found in {TEMPLATES_DIR}", status_code=404)
        
    return templates.TemplateResponse(
        "service.html",
        {"request": request, "title": "Service & Workshop"}
    )