import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Request
from pwdlib import PasswordHash

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5
EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_HOURS = 8

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

def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)

def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=REFRESH_TOKEN_EXPIRE_HOURS)

def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None

async def user_identifier(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = jwt.decode(auth[7:], os.getenv("JWT_SECRET_KEY"), algorithms=[ALGORITHM])
            if payload.get("sub") and payload.get("purpose") == "access":
                return f"user:{payload['sub']}"
        except jwt.PyJWTError:
            pass
    return f"ip:{get_client_ip(request) or 'unknown'}"
