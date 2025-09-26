from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_connection, get_db_manager
from app.db.base_manager import AbstractDBManager
from app.db.sqlalchemy.manager import SQLAlchemyManager
from app.domain.repositories.iresource_repository import IResourceRepository
from app.infrastructure.repositories.sqlalchemy.resource_repository import SQLAlchemyResourceRepository


async def get_resource_repo(
        conn: AsyncSession = Depends(get_connection),
        db_manager: AbstractDBManager = Depends(get_db_manager)
) -> IResourceRepository:
    if isinstance(db_manager, SQLAlchemyManager):
        return SQLAlchemyResourceRepository(conn)
    else:
        raise RuntimeError("Unknown DB manager")
