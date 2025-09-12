from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlalchemy.models import User
from app.infrastructure.exceptions.exceptions import IntegrityViolationException
from app.exceptions.users_exceptions.email_already_exists_exception import EmailAlreadyExistsException
from app.exceptions.users_exceptions.username_already_exists_exception import UsernameAlreadyExistsException
from app.infrastructure.mappers.sqlalchemy.user_mapper import UserMapper
from app.domain.repositories.iuser_repository import IUserRepository
from app.domain.schemas.user.user import UserCreate, UserRead, UserUpdate, UserReadInternal
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

    async def get_by_email(self, email: str) -> Optional[UserRead]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        orm_user = result.scalar_one_or_none()
        return self.mapper.to_read(orm_user) if orm_user else None

    async def get_internal_by_username(self, username: str) -> Optional[UserReadInternal]:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        orm_user = result.scalar_one_or_none()
        return UserReadInternal.model_validate(orm_user) if orm_user else None

    async def create(self, create_schema: UserCreate) -> UserRead:
        try:
            return await super().create(create_schema)
        except IntegrityViolationException as e:
            err = str(e).lower()
            if "username" in err:
                raise UsernameAlreadyExistsException("Username already exists in the system")
            elif "email" in err:
                raise EmailAlreadyExistsException("Email address already exists in the system")
            raise

    async def update(self, obj_id: int, update_schema: UserUpdate) -> Optional[UserRead]:
        try:
            return await super().update(obj_id, update_schema)
        except IntegrityViolationException as e:
            err = str(e).lower()
            if "username" in err:
                raise UsernameAlreadyExistsException("Username already exists in the system")
            elif "email" in err:
                raise EmailAlreadyExistsException("Email address already exists in the system")
            raise