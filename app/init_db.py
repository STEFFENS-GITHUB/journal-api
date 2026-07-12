import asyncio
from app.utils.database import create_db_engine
from app.main import init_db, validate_env

if __name__ == "__main__":
    validate_env()
    engine, session_factory = create_db_engine()
    asyncio.run(init_db(engine, session_factory))
