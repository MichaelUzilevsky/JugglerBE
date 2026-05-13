from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_connection, get_db_manager
from app.db.base_manager import AbstractDBManager
from app.db.sqlalchemy.manager import SQLAlchemyManager
from app.domain.repositories.ijwt_token_repository import IJwtTokenRepository
from app.infrastructure.repositories.sqlalchemy.jwt_token_repository import SQLAlchemyJwtTokenRepository


async def get_jwt_repo(
        conn: AsyncSession = Depends(get_connection),
        db_manager: AbstractDBManager = Depends(get_db_manager)
) -> IJwtTokenRepository:
    if isinstance(db_manager, SQLAlchemyManager):
        return SQLAlchemyJwtTokenRepository(conn)
    else:
        raise RuntimeError("Unknown DB manager")
