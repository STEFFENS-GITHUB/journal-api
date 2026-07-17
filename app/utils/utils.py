import hashlib
import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5
EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS = 24

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "purpose": "access", "exp": expire}, os.getenv("JWT_SECRET_KEY"), algorithm=ALGORITHM)

def create_email_verification_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": str(user_id), "purpose": "email-verify", "exp": expire}, os.getenv("JWT_SECRET_KEY"), algorithm=ALGORITHM)

def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
