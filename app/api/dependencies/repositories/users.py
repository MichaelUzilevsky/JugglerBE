from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_session
from app.domain.repositories.iuser_repository import IUserRepository
from app.infrastructure.repositories.sqlalchemy.user_repository import SQLAlchemyUserRepository


async def get_user_repo(session: AsyncSession = Depends(get_session)) -> IUserRepository:
    return SQLAlchemyUserRepository(session)
