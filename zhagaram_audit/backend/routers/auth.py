from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User 
from ..schemas import LoginData, Token
from .. import auth as auth_helper 

router = APIRouter()

@router.post("/login", response_model=Token)
def login_for_access_token(data: LoginData, db: Session = Depends(get_db)):
    # DEBUG: See what the frontend is sending
    print(f"--- LOGIN ATTEMPT: {data.username} ---")
    
    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        print(f"DEBUG: User '{data.username}' not found in the 'users' table.")
        raise HTTPException(status_code=401, detail="User not found")

    # EMERGENCY BACKDOOR: If this works, your DB hash is the only problem.
    if data.username == "admin" and data.password == "admin123":
        print("DEBUG: Emergency login successful. Redirecting...")
        access_token = auth_helper.create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}

    # Standard check (the part that has been failing)
    if not auth_helper.verify_password(data.password, user.password):
        print(f"DEBUG: Hash verification failed for {data.username}")
        raise HTTPException(status_code=401, detail="Hash mismatch")

    access_token = auth_helper.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

