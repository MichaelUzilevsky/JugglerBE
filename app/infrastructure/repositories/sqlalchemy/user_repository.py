from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlalchemy.models import User
from app.infrastructure.mappers.sqlalchemy.user_mapper import UserMapper
from app.domain.repositories.iuser_repository import IUserRepository
from app.domain.schemas.user.user import UserCreate, UserRead, UserUpdate
from app.infrastructure.repositories.sqlalchemy.base_repository import SQLAlchemyBaseRepository


class SQLAlchemyUserRepository(
    SQLAlchemyBaseRepository[UserRead, UserCreate, UserUpdate, User],
    IUserRepository,
):
    """
    User repository specialized for SQLAlchemy,
    extends the base repository with domain-specific methods if needed.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, User, UserMapper)

    async def get_by_username(self, username: str) -> Optional[UserRead]:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        orm_user = result.scalar_one_or_none()
        return self.mapper.to_read(orm_user) if orm_user else None
