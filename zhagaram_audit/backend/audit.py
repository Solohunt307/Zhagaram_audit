from .database import SessionLocal
from .models import AuditLog

def log_action(user_id, action, table_name, record_id):
    db = SessionLocal()
    log = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id
    )
    db.add(log)
    db.commit()
    db.close()
