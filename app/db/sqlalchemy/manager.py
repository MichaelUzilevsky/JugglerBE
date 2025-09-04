from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app import config, logger

postgresql_config = config.get_value("postgresql")
DATA_BASE_URL = (
    f"postgresql+asyncpg://"
    f"{postgresql_config['user']}:{postgresql_config['password']}@"
    f"{postgresql_config['host']}:{postgresql_config['port']}/"
    f"{postgresql_config['database']}"
)

class SQLAlchemyManager:
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
            logger.info("[SQLAlchemyManager] Initialized SQLAlchemy Manager")

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        async with self._session_maker() as session:
            yield session

    async def close(self):
        await self._engine.dispose()
        logger.info("[SQLAlchemyManager] Closed SQLAlchemy Manager")
