from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_connection, get_db_manager
from app.db.base_manager import AbstractDBManager
from app.db.sqlalchemy.manager import SQLAlchemyManager
from app.domain.repositories.iuser_repository import IUserRepository
from app.infrastructure.repositories.sqlalchemy.user_repository import SQLAlchemyUserRepository


async def get_user_repo(
        conn: AsyncSession = Depends(get_connection),
        db_manager: AbstractDBManager = Depends(get_db_manager)
) -> IUserRepository:
    if isinstance(db_manager, SQLAlchemyManager):
        return SQLAlchemyUserRepository(conn)
    else:
        raise RuntimeError("Unknown DB manager")
