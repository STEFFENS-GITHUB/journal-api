from app.models.journal import Journal, JournalIn, JournalOut, JournalSummary, JournalUpdate
from app.models.user import User
from app.database.session import get_session
from app.routers.auth import get_current_user
from typing import Annotated
from fastapi import Depends, HTTPException, APIRouter, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/journal")

@router.post('/create', response_model=JournalOut, status_code=status.HTTP_201_CREATED)
async def create_journal(session: Annotated[AsyncSession, Depends(get_session)],
                  user: Annotated[User, Depends(get_current_user)],
                new_journal: JournalIn):
    journal = Journal(**new_journal.model_dump(), user_id=user.id)
    session.add(journal)
    await session.commit()
    await session.refresh(journal)
    return journal

@router.delete('/{id}', status_code=204)
async def delete_journal(session: Annotated[AsyncSession, Depends(get_session)],
                  user: Annotated[User, Depends(get_current_user)],
                 id: int):
    journal = await session.get(Journal, id)
    if not journal or journal.user_id != user.id:
        raise HTTPException(status_code=404, detail="Journal not found")
    await session.delete(journal)
    await session.commit()

@router.put('/{id}', response_model=JournalOut)
async def replace_journal(session: Annotated[AsyncSession, Depends(get_session)],
                    user: Annotated[User, Depends(get_current_user)],
                 id: int, new_journal: JournalIn):
    journal = await session.get(Journal, id)
    if not journal or journal.user_id != user.id:
        raise HTTPException(status_code=404, detail="Journal not found")
    new_data = new_journal.model_dump()
    for key in new_data:
        setattr(journal, key, new_data[key])
    await session.commit()
    await session.refresh(journal)
    return journal

@router.patch('/{id}', response_model=JournalOut)
async def update_journal(session: Annotated[AsyncSession, Depends(get_session)],
                   user: Annotated[User, Depends(get_current_user)],
                   id: int, updated_journal: JournalUpdate):
    journal = await session.get(Journal, id)
    if not journal or journal.user_id != user.id:
        raise HTTPException(status_code=404, detail="Journal not found")
    new_data = updated_journal.model_dump(exclude_unset=True)
    for key in new_data:
        setattr(journal, key, new_data[key])
    await session.commit()
    await session.refresh(journal)
    return journal

@router.get('', response_model=list[JournalSummary])
@router.get('/', response_model=list[JournalSummary])
async def get_journals(session: Annotated[AsyncSession, Depends(get_session)],
                  user: Annotated[User, Depends(get_current_user)]):
    query = select(Journal).where(Journal.user_id == user.id)
    result = await session.execute(query)
    return result.scalars().all()

@router.get('/{id}', response_model=JournalOut)
async def get_journal(session: Annotated[AsyncSession, Depends(get_session)],
                  user: Annotated[User, Depends(get_current_user)],
                  id: int):
    query = select(Journal).options(selectinload(Journal.user)).where(Journal.id == id)
    result = await session.execute(query)
    journal = result.scalars().one_or_none()
    if not journal or journal.user_id != user.id:
        raise HTTPException(status_code=404, detail="Journal not found")
    return journal