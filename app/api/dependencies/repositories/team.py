from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_connection, get_db_manager
from app.db.base_manager import AbstractDBManager
from app.db.sqlalchemy.manager import SQLAlchemyManager
from app.domain.repositories.iteam_repository import ITeamRepository
from app.infrastructure.repositories.sqlalchemy.team_repository import SQLAlchemyTeamRepository


async def get_team_repo(
        conn: AsyncSession = Depends(get_connection),
        db_manager: AbstractDBManager = Depends(get_db_manager)
) -> ITeamRepository:
    if isinstance(db_manager, SQLAlchemyManager):
        return SQLAlchemyTeamRepository(conn)
    else:
        raise RuntimeError("Unknown DB manager")
