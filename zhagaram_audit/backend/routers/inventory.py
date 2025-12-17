from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import InventoryMovement
from ..audit import log_action

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/inventory/move")
def stock_movement(
    product_id: int,
    movement_type: str,
    quantity: int,
    serial_number: str = None,
    remarks: str = "",
    db: Session = Depends(get_db)
):
    movement = InventoryMovement(
        product_id=product_id,
        movement_type=movement_type,
        quantity=quantity,
        serial_number=serial_number,
        remarks=remarks
    )
    db.add(movement)
    db.commit()

    log_action(1, "STOCK_MOVE", "inventory_movements", product_id)
    return {"message": "Stock updated"}
