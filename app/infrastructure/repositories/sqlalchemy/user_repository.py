from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.sqlalchemy.models import User
from app.domain.exceptions.repository_exceptions import IntegrityViolationException, NotFoundException, \
    RepositoryException
from app.domain.repositories.iuser_repository import IUserRepository
from app.domain.schemas.user.user import UserCreate, UserRead, UserUpdate, UserReadInternal
from app.exceptions.users_exceptions.users_exceptions import UsernameAlreadyExistsException, \
    EmailAlreadyExistsException, UserNotFoundException
from app.infrastructure.mappers.sqlalchemy.user_mapper import UserMapper
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

    def _default_options(self) -> list:
        return [selectinload(User.team)]

    async def get_by_username(self, username: str) -> Optional[UserRead]:
        try:
            stmt = select(User).where(User.username == username).options(selectinload(User.team))
            result = await self.session.execute(stmt)
            orm_user = result.scalar_one_or_none()

            if orm_user:
                self._log_debug(
                    "get_by_username_success",
                    extra={
                        "username": username,
                        "user_id": orm_user.id,
                    }
                )
                return self.mapper.to_read(orm_user)

            self._log_warning(
                "get_by_username_not_found",
                extra={
                    "username": username,
                }
            )
            return

        except SQLAlchemyError as e:
            self._log_error(
                "get_by_username_error",
                extra={
                    "username": username,
                    "error": str(e),
                }
            )
            raise RepositoryException()

    async def get_by_email(self, email: str) -> Optional[UserRead]:
        try:
            stmt = select(User).where(User.email == email).options(selectinload(User.team))
            result = await self.session.execute(stmt)
            orm_user = result.scalar_one_or_none()

            if orm_user:
                self._log_debug(
                    "get_by_email_success",
                    msg=f"User found with email={email}",
                    extra={
                        "email": email,
                        "user_id": orm_user.id,
                    }
                )
                return self.mapper.to_read(orm_user)

            self._log_warning(
                "get_by_email_not_found",
                msg=f"No user found with email={email}",
                extra={
                    "email": email,
                }
            )
            return

        except SQLAlchemyError as e:
            self._log_error("get_by_email_error",
                            msg=f"Error fetching user by email={email}",
                            extra={
                                "email": email,
                                "error": str(e),
                            }
                            )
            raise RepositoryException()

    async def get_internal_by_username(self, username: str) -> Optional[UserReadInternal]:
        try:
            stmt = select(User).where(User.username == username).options(selectinload(User.team))
            result = await self.session.execute(stmt)
            orm_user = result.scalar_one_or_none()

            if orm_user:
                self._log_debug("get_internal_by_username_success",
                               msg=f"Internal user fetched for username={username}",
                               extra={
                                   "username": username,
                                   "user_id": orm_user.id,
                               }
                               )
                return UserReadInternal.model_validate(orm_user)

            self._log_warning("get_internal_by_username_not_found",
                              msg=f"No internal user found with username={username}",
                              extra={
                                  "username": username,
                              })
            return

        except SQLAlchemyError as e:
            self._log_error("get_internal_by_username_error",
                            msg=f"Error fetching internal user by username={username}",
                            extra={
                                "username": username,
                                "error": str(e),
                            })
            raise RepositoryException()

    async def create(self, create_schema: UserCreate) -> UserRead:
        try:
            user = await super().create(create_schema)
            self._log_debug("user_created",
                           msg=f"User created with username={create_schema.username}",
                           extra={"username": create_schema.username, "user_id": user.id})
            return user

        except IntegrityViolationException as e:
            err = str(e).lower()
            if "username" in err:
                raise UsernameAlreadyExistsException("Username already exists")
            if "email" in err:
                raise EmailAlreadyExistsException("Email already exists")
            raise

    async def update(self, obj_id: int, update_schema: UserUpdate) -> Optional[UserRead]:
        try:
            user = await super().update(obj_id, update_schema)
            self._log_debug("user_updated",
                           msg=f"User updated with id={obj_id}",
                           extra={"user_id": obj_id})
            return user

        except IntegrityViolationException as e:
            err = str(e).lower()
            if "username" in err:
                raise UsernameAlreadyExistsException("Username already exists")
            if "email" in err:
                raise EmailAlreadyExistsException("Email already exists")
            raise

        except NotFoundException:
            raise UserNotFoundException(f"User with id={obj_id} not found")
