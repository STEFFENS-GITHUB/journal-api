import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.database.session import get_session, AsyncSessionLocal
from app.models.user import UserOut, User

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Missing JWT_SECRET_KEY env var")
DEFAULT_USER = os.getenv("DEFAULT_USER")
DEFAULT_USER_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD")
if not DEFAULT_USER or not DEFAULT_USER_PASSWORD:
    raise RuntimeError("Missing DEFAULT_USER or DEFAULT_USER_PASSWORD env var")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

router = APIRouter()
password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)],
                 session: Annotated[AsyncSession, Depends(get_session)]):
    query = select(User).where(User.username == form_data.username)
    result = await session.execute(query)
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username or password is incorrect")
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}

async def get_current_user(token: Annotated[str | None, Depends(OAuth2PasswordBearer(tokenUrl="/login", auto_error=False))],
                            session: Annotated[AsyncSession, Depends(get_session)]):
    unauthenticated_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="You are not logged in",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise unauthenticated_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired, please log in again",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await session.get(User, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your account no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserOut.model_validate(user)

async def create_default_user():
    async with AsyncSessionLocal() as session:
        query = select(User).where(User.username == DEFAULT_USER)
        result = await session.execute(query)
        user = result.scalars().first()
        if not user:
            user = User(username=DEFAULT_USER, password_hash=hash_password(DEFAULT_USER_PASSWORD))
            session.add(user)
            await session.commit()
