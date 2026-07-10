from app.models.base import Base
from app.routers.auth import create_default_user
from app.routers import journal, user, auth
from app.middleware.logging import LoggingMiddleware
from app.session import config_init
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from sqlalchemy import text

async def init_db(engine, session_factory):
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
    await create_default_user(session_factory)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine, app.state.session_factory = config_init()
    await init_db(app.state.engine, app.state.session_factory)
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