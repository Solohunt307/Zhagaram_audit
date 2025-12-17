# create_admin.py
from backend.database import SessionLocal, engine
from backend import models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if admin exists
    admin_exists = db.query(models.User).filter(models.User.username == "admin").first()
    
    if not admin_exists:
        # Use the exact column names from your User model
        new_admin = models.User(
            username="admin",
            hashed_password=pwd_context.hash("admin123"),
            full_name="Administrator",
            is_active=True,  # Now valid because we updated models.py
            is_admin=True
        )
        db.add(new_admin)
        db.commit()
        print("Admin user 'admin' created successfully!")
    else:
        print("Admin user already exists.")
    db.close()

if __name__ == "__main__":
    init_db()