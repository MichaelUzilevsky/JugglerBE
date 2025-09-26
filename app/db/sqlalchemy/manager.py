import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app import config, logger
from app.db.base_manager import AbstractDBManager

postgresql_config = config.get_value("postgresql")
DATA_BASE_URL = (
    f"postgresql+asyncpg://"
    f"{postgresql_config['user']}:{postgresql_config['password']}@"
    f"{postgresql_config['host']}:{postgresql_config['port']}/"
    f"{postgresql_config['database']}"
)


class SQLAlchemyManager(AbstractDBManager):
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._engine = create_async_engine(
                DATA_BASE_URL,
                echo=postgresql_config.get("echo", False),
                future=True
            )
            self._session_maker = async_sessionmaker(
                self._engine,
                expire_on_commit=False,
                class_=AsyncSession
            )
            self._initialized = True
            logger.info("Initialized SQLAlchemy Manager")

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_maker() as session:
            yield session

    @asynccontextmanager
    async def transaction(self, session: AsyncSession):
        try:
            yield session
            await session.commit()  # commit if no exception
        except Exception:
            await session.rollback()
            raise

    async def check_connection(self, timeout: float = 3.0) -> bool:
        try:
            async def _check():
                async with self.get_connection() as session:
                    await session.execute(text("SELECT 1"))

            await asyncio.wait_for(_check(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.error(f"DB connection check timed out after {timeout} seconds", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"DB connection check failed: {e}", exc_info=True)
            return False

    @property
    def raw(self) -> Any:
        return self._engine

    async def close(self):
        await self._engine.dispose()
        logger.info("Closed SQLAlchemy Manager")
