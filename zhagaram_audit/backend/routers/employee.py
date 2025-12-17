from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Employee
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter(prefix="/api/employees", tags=["Employees"])

class EmployeeCreate(BaseModel):
    name: str
    role: str
    phone: Optional[str] = None
    email: Optional[str] = None

@router.post("/")
def create_employee(emp: EmployeeCreate, db: Session = Depends(get_db)):
    try:
        new_emp = Employee(
            name=emp.name,
            role=emp.role,
            phone=emp.phone,
            email=emp.email,
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_emp)
        db.commit()
        db.refresh(new_emp)
        return new_emp
    except Exception as e:
        db.rollback()
        print(f"Database Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    return [{
        "id": e.id,
        "name": e.name,
        "role": e.role,
        "phone": e.phone or "N/A",
        "email": e.email or "N/A"
    } for e in employees]

@router.put("/{emp_id}")
def update_employee(emp_id: int, emp: EmployeeCreate, db: Session = Depends(get_db)):
    db_emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not db_emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    try:
        db_emp.name = emp.name
        db_emp.role = emp.role
        db_emp.phone = emp.phone
        db_emp.email = emp.email
        db.commit()
        return db_emp
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(emp)
    db.commit()
    return {"message": "Deleted"}