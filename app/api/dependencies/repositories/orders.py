from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_session
from app.domain.repositories.iorder_repository import IOrderRepository
from app.infrastructure.repositories.sqlalchemy.order_repository import SQLAlchemyOrderRepository


async def get_order_repo(session: AsyncSession = Depends(get_session)) -> IOrderRepository:
    return SQLAlchemyOrderRepository(session)
