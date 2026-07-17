import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.utils.database import get_session
from app.utils.queue import send_email_verification_message
from app.models.refresh import RefreshRequest, RefreshToken
from app.models.user import UserIn, UserOut, User
from app.utils.utils import (ALGORITHM, create_access_token, create_email_verification_token,
                             hash_password, hash_refresh_token, verify_password)

REFRESH_TOKEN_EXPIRE_HOURS = 8

router = APIRouter()

async def issue_refresh_token(user_id: int, session: AsyncSession) -> str:
    raw = secrets.token_urlsafe(32)
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=REFRESH_TOKEN_EXPIRE_HOURS)
    session.add(RefreshToken(user_id=user_id, token_hash=hash_refresh_token(raw), expires_at=expire))
    await session.commit()
    return raw

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(newUser: UserIn,
                   request: Request,
                   session: Annotated[AsyncSession, Depends(get_session)]):
    user = User(username=newUser.username, email=newUser.email, password_hash=hash_password(newUser.password))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already taken")
    await session.refresh(user)
    token = create_email_verification_token(user.id)
    await send_email_verification_message(request.app.state.sqs_client, user.id, user.email, token)
    return user

@router.get("/verify-email")
async def verify_email(token: str,
                       session: Annotated[AsyncSession, Depends(get_session)]):
    invalid_token_exception = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token has expired")
    except jwt.PyJWTError:
        raise invalid_token_exception

    if payload.get("purpose") != "email-verify" or payload.get("sub") is None:
        raise invalid_token_exception

    user = await session.get(User, int(payload["sub"]))
    if user is None:
        raise invalid_token_exception

    user.email_verified = True
    await session.commit()
    return {"detail": "Email verified"}

@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)],
                 session: Annotated[AsyncSession, Depends(get_session)]):
    query = select(User).where(or_(User.username == form_data.username, User.email == form_data.username))
    result = await session.execute(query)
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username or password is incorrect")
    if not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email before logging in")
    return {"access_token": create_access_token(user.id),
            "refresh_token": await issue_refresh_token(user.id, session),
            "token_type": "bearer"}

@router.post("/refresh-token")
async def refresh(body: RefreshRequest,
                  session: Annotated[AsyncSession, Depends(get_session)]):
    invalid_token_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    query = select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(body.refresh_token))
    result = await session.execute(query)
    stored = result.scalars().first()

    if stored is None:
        raise invalid_token_exception
    if stored.revoked:
        await session.execute(update(RefreshToken).where(RefreshToken.user_id == stored.user_id).values(revoked=True))
        await session.commit()
        raise invalid_token_exception
    if stored.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise invalid_token_exception

    stored.revoked = True
    return {"access_token": create_access_token(stored.user_id),
            "refresh_token": await issue_refresh_token(stored.user_id, session),
            "token_type": "bearer"}

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest,
                 session: Annotated[AsyncSession, Depends(get_session)]):
    await session.execute(update(RefreshToken)
                          .where(RefreshToken.token_hash == hash_refresh_token(body.refresh_token))
                          .values(revoked=True))
    await session.commit()

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
        if user_id is None or payload.get("purpose") != "access":
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
            user = User(username=os.getenv("DEFAULT_USER"), password_hash=hash_password(os.getenv("DEFAULT_USER_PASSWORD")), email_verified=True)
            session.add(user)
            await session.commit()
