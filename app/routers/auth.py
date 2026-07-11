import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.session import get_session
from app.models.user import UserIn, UserOut, User
from app.utils.utils import hash_password, verify_password

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

router = APIRouter()

def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, os.getenv("JWT_SECRET_KEY"), algorithm=ALGORITHM)

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(newUser: UserIn,
                   session: Annotated[AsyncSession, Depends(get_session)]):
    user = User(username=newUser.username, password_hash=hash_password(newUser.password))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    await session.refresh(user)
    return user

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
        payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=[ALGORITHM])
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

async def get_current_user_optional(token: Annotated[str | None, Depends(OAuth2PasswordBearer(tokenUrl="/login", auto_error=False))],
                                     session: Annotated[AsyncSession, Depends(get_session)]):
    if token is None:
        return None
    return await get_current_user(token, session)

async def create_default_user(session_factory):
    async with session_factory() as session:
        query = select(User).where(User.username == os.getenv("DEFAULT_USER"))
        result = await session.execute(query)
        user = result.scalars().first()
        if not user:
            user = User(username=os.getenv("DEFAULT_USER"), password_hash=hash_password(os.getenv("DEFAULT_USER_PASSWORD")))
            session.add(user)
            await session.commit()
