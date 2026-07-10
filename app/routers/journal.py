from app.models.journal import Journal, JournalIn, JournalOut, JournalSummary, JournalUpdate
from app.models.user import User
from app.session import get_session
from app.routers.auth import get_current_user, get_current_user_optional
from typing import Annotated
from fastapi import Depends, HTTPException, APIRouter, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/journal")

def _check_journal_access(journal: Journal | None, user: User | None, allow_public: bool = False) -> None:
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    if allow_public and journal.is_public:
        return
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="You are not logged in",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if journal.user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this journal")

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
    _check_journal_access(journal, user)
    await session.delete(journal)
    await session.commit()

@router.put('/{id}', response_model=JournalOut)
async def replace_journal(session: Annotated[AsyncSession, Depends(get_session)],
                    user: Annotated[User, Depends(get_current_user)],
                 id: int, new_journal: JournalIn):
    journal = await session.get(Journal, id)
    _check_journal_access(journal, user)
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
    _check_journal_access(journal, user)
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

@router.get('/index', response_model=list[JournalSummary])
async def get_journal_index(session: Annotated[AsyncSession, Depends(get_session)],
                             after_id: int = 0):
    query = (
        select(Journal.id, Journal.title, Journal.is_public)
        .where(Journal.id > after_id)
        .order_by(Journal.id)
        .limit(50)
    )
    result = await session.execute(query)
    return [
        JournalSummary(id=id, title=title if is_public else "Private", is_public=is_public)
        for id, title, is_public in result.all()
    ]

@router.get('/{id}', response_model=JournalOut)
async def get_journal(session: Annotated[AsyncSession, Depends(get_session)],
                  user: Annotated[User | None, Depends(get_current_user_optional)],
                  id: int):
    query = select(Journal).where(Journal.id == id)
    result = await session.execute(query)
    journal = result.scalars().one_or_none()
    _check_journal_access(journal, user, allow_public=True)
    return journal