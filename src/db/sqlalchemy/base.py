from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src import config

postgresql_config = config.get_value("postgresql")

DATA_BASE_URL = (
    f"postgresql+asyncpg://"
    f"{postgresql_config['user']}:{postgresql_config['password']}@"
    f"{postgresql_config['host']}:{postgresql_config['port']}/"
    f"{postgresql_config['database']}"
)

engine = create_async_engine(
    DATA_BASE_URL,
    echo=postgresql_config.get("echo", False),
    pool_size=postgresql_config.get("pool_size", 10),
    max_overflow=postgresql_config.get("max_overflow", 20),
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()
