from sqlalchemy.ext.asyncio import create_async_engine

from app import config
from app.db.sqlalchemy.models import *
from app.db.sqlalchemy.base import Base

postgresql_config = config.get_value("postgresql")
DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{postgresql_config['user']}:{postgresql_config['password']}@"
    f"{postgresql_config['host']}:{postgresql_config['port']}/"
    f"{postgresql_config['database']}"
)

engine = create_async_engine(DATABASE_URL, echo=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

import asyncio
asyncio.run(init_db())
