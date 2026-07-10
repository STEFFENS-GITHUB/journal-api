from app.models.journal import Journal, JournalIn, JournalOut
from app.session import get_session
from app.models.user import User, UserIn, UserOut
from app.utils.utils import hash_password
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import Depends, HTTPException, APIRouter, status
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/user")

@router.post('/create', response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(session: Annotated[AsyncSession, Depends(get_session)],
                newUser: UserIn):
    user_data = newUser.model_dump()
    user_data["password_hash"] = hash_password(user_data.pop("password")) 
    user = User(**user_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@router.get('/{id}', response_model=UserOut)
async def get_user(session: Annotated[AsyncSession, Depends(get_session)],
                  user: Annotated[User, Depends(get_current_user)],
                  id: int):
    if id != user.id:
        raise HTTPException(status_code=404, detail="User not found")
    query = select(User).options(selectinload(User.journals)).where(User.id == id)
    result = await session.execute(query)
    user = result.scalars().one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete('/{id}', status_code=204)
async def delete_user(session: Annotated[AsyncSession, Depends(get_session)],
                  user: Annotated[User, Depends(get_current_user)],
                 id: int):
    if id != user.id:
        raise HTTPException(status_code=404, detail="User not found")
    user = await session.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()