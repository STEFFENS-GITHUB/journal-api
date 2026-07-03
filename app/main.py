from app.database.session import engine, get_session
from app.models.base import Base
from app.routers.auth import create_default_user
from app.routers import journal, user, auth
from app.middleware.logging import LoggingMiddleware
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
import uvicorn
import asyncio 
from sqlalchemy import text

async def init_db():
    for _ in range (30):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                break
        except Exception:
            await asyncio.sleep(2)
    else:
        raise RuntimeError("DB connection has failed.")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await create_default_user()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)
app.include_router(journal.router)
app.include_router(user.router)
app.include_router(auth.router)

@app.get('/')
def index():
    return f"Welcome to the page"

@app.get("/health", status_code=200)
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000
    )