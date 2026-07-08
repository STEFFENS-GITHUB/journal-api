from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.models.user import UserOut
from pydantic import BaseModel, ConfigDict, Field

class JournalIn(BaseModel):
    title: str
    body: str
    is_public: bool = False

class JournalUpdate(BaseModel):
    title: str | None = Field(default=None)
    body: str | None = Field(default=None)
    is_public: bool | None = Field(default=None)

class JournalOut(BaseModel):
    title: str
    body: str
    id: int
    is_public: bool
    model_config = ConfigDict(from_attributes=True)

class JournalSummary(BaseModel):
    id: int
    title: str
    is_public: bool
    model_config = ConfigDict(from_attributes=True)

class Journal(Base):
    __tablename__ = "journal"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    body: Mapped[str] = mapped_column(String(255), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="journals")

