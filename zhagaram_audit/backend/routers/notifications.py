from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Notification, Customer
from ..audit import log_action
from datetime import datetime
import requests

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def send_sms(phone: str, message: str):
    # Twilio example (replace with your credentials)
    TWILIO_SID = "YOUR_TWILIO_SID"
    TWILIO_AUTH = "YOUR_TWILIO_AUTH_TOKEN"
    TWILIO_FROM = "YOUR_TWILIO_NUMBER"

    # Here you would integrate Twilio API call
    # For demo, just print
    print(f"SMS to {phone}: {message}")
    return True


def send_whatsapp(phone: str, message: str):
    # WhatsApp Cloud API or Twilio WhatsApp
    print(f"WhatsApp to {phone}: {message}")
    return True

@router.post("/send_notification")
def send_notification(customer_id: int, notif_type: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return {"error": "Customer not found"}

    if notif_type == "INVOICE":
        message = f"Hello {customer.name}, your invoice is generated."
    elif notif_type == "SERVICE_READY":
        message = f"Hello {customer.name}, your service is ready for pickup."
    elif notif_type == "WARRANTY":
        message = f"Hello {customer.name}, your product warranty is about to expire."
    else:
        return {"error": "Invalid notification type"}

    # Send SMS / WhatsApp
    sms_status = send_sms(customer.phone, message)
    wa_status = send_whatsapp(customer.phone, message)

    status = "SENT" if sms_status and wa_status else "FAILED"

    notif = Notification(
        customer_id=customer_id,
        type=notif_type,
        message=message,
        status=status,
        sent_at=datetime.now()
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    log_action(1, f"SEND_NOTIFICATION_{notif_type}", "notifications", notif.id)
    return {"message": f"Notification {status}", "notification_id": notif.id}

