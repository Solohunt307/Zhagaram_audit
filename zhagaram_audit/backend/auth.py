from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt

# Setup Bcrypt hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "ZHAGARAM_SECRET_KEY_2025" 
ALGORITHM = "HS256"

def verify_password(plain_password, hashed_password):
    # Validates input against the $2b$ hash in DB
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    # Corrected for Python 3.13 timezone awareness
    expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)