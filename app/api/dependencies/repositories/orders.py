from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_connection, get_db_manager
from app.db.base_manager import AbstractDBManager
from app.db.sqlalchemy.manager import SQLAlchemyManager
from app.domain.repositories.iorder_repository import IOrderRepository
from app.infrastructure.repositories.sqlalchemy.order_repository import SQLAlchemyOrderRepository


async def get_order_repo(
        conn: AsyncSession = Depends(get_connection),
        db_manager: AbstractDBManager = Depends(get_db_manager)) -> IOrderRepository:
    if isinstance(db_manager, SQLAlchemyManager):
        return SQLAlchemyOrderRepository(conn)
    else:
        raise RuntimeError("Unknown DB manager")
