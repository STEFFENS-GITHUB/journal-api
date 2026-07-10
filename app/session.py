import os, json

from fastapi import Request
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

def config_init():
    for var in ("JWT_SECRET_KEY", "DEFAULT_USER", "DEFAULT_USER_PASSWORD"):
        if not os.getenv(var):
            raise RuntimeError(f"Missing {var} env var")

    if os.getenv("DATABASE_URL"):
        db_url = os.getenv("DATABASE_URL")
    else:
        secret = os.getenv("DB_MASTER_SECRET")
        if not secret:
            raise RuntimeError("Missing DB configuration. (Missing required env vars)")
        secret_json = json.loads(secret)
        host = os.getenv("DB_ENDPOINT")
        dbname = os.getenv("DB_NAME")
        if not host or not dbname:
            raise RuntimeError("Missing DB env vars")
        db_url = f"mysql+asyncmy://{secret_json['username']}:{secret_json['password']}@{host}/{dbname}"

    engine = create_async_engine(db_url, echo=True, poolclass=NullPool)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    return engine, factory

async def get_session(request: Request):
    factory = request.app.state.session_factory
    async with factory() as session:
        yield session
