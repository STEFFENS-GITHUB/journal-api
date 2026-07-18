from app.models.base import Base
from app.routers.auth import create_default_user
from app.routers import journal, user, auth
from app.middleware.logging import LoggingMiddleware
from app.utils.database import create_db_engine
from app.utils.queue import create_sqs_client
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import os
from sqlalchemy import text

def validate_env():
    for var in ("JWT_SECRET_KEY", "DEFAULT_USER", "DEFAULT_USER_PASSWORD"):
        if not os.getenv(var):
            raise RuntimeError(f"Missing {var} env var")

    if not os.getenv("DATABASE_URL"):
        for var in ("DB_MASTER_SECRET", "DB_ENDPOINT", "DB_NAME"):
            if not os.getenv(var):
                raise RuntimeError(f"Missing {var} env var (required when DATABASE_URL is not set)")

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
    validate_env()
    app.state.engine, app.state.session_factory = create_db_engine()
    app.state.sqs_client = create_sqs_client()
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

@app.get("/health")
async def health(request: Request):
    checks = {}
    try:
        async with request.app.state.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    try:
        await asyncio.to_thread(request.app.state.sqs_client.list_queues, MaxResults=1)
        checks["queue"] = "ok"
    except Exception:
        checks["queue"] = "unavailable"

    # Queue is best-effort throughout the app, so it reports but does
    # not fail the health status.
    if checks["database"] == "ok":
        return {"status": "healthy", "checks": checks}
    raise HTTPException(status_code=503, detail={"status": "unhealthy", "checks": checks})

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000
    )