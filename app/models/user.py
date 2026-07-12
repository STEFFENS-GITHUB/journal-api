from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserIn(BaseModel):
    username: str = Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=3)

class UserOut(BaseModel):
    username: str
    id: int
    model_config = ConfigDict(from_attributes=True)

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), unique=True, index=True, nullable=True)
    email_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    journals: Mapped[list["Journal"]] = relationship("Journal", back_populates="user")