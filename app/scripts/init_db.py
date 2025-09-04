from sqlalchemy.ext.asyncio import create_async_engine
from src.db.sqlalchemy.models import *
from src.db.sqlalchemy.base import Base

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


DATABASE_URL = "postgresql+asyncpg://admin:admin@localhost/juggler"

engine = create_async_engine(DATABASE_URL, echo=True)

async def reset_db():
    async with engine.begin() as conn:
        # Drop all tables first
        await conn.run_sync(Base.metadata.drop_all)

import asyncio
asyncio.run(init_db())
