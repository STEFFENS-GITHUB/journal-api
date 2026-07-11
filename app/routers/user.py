from app.models.journal import Journal, JournalIn, JournalOut
from app.session import get_session
from app.models.user import User, UserOut
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import Depends, HTTPException, APIRouter
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/user")

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