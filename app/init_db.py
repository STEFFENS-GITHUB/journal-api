import asyncio
from app.session import config_init
from app.main import init_db

if __name__ == "__main__":
    engine, session_factory = config_init()
    asyncio.run(init_db(engine, session_factory))
