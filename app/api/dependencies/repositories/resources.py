from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_session
from app.domain.repositories.iresource_repository import IResourceRepository
from app.infrastructure.repositories.sqlalchemy.resource_repository import SQLAlchemyResourceRepository


async def get_resource_repo(session: AsyncSession = Depends(get_session)) -> IResourceRepository:
    return SQLAlchemyResourceRepository(session)
