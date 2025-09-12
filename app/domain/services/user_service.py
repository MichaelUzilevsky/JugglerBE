from typing import Optional, List

from app.infrastructure.exceptions.exceptions import NotFoundException
from app.domain.repositories.iuser_repository import IUserRepository
from app import logger
from app.domain.schemas.user.enums.user_role import UserRole
from app.domain.schemas.user.user import UserCreate, UserRead, UserUpdate
from app.exceptions.users_exceptions.email_already_exists_exception import EmailAlreadyExistsException
from app.exceptions.users_exceptions.login_failed_exception import LoginFailedException
from app.exceptions.users_exceptions.user_not_found_exception import UserNotFoundException
from app.exceptions.users_exceptions.username_already_exists_exception import UsernameAlreadyExistsException
from app.utils.password_security import hash_password, verify_password


class UserService:
    """
    Service layer for user operations.
    Handles business logic, password hashing, validation, and role changes.
    """

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo


    async def get_by_username(self, username: str) -> Optional[UserRead]:
        return await self.user_repo.get_by_username(username)


    async def list_users(self) -> List[UserRead]:
        return await self.user_repo.list()


    async def signup(self, user_create: UserCreate) -> UserRead:
        logger.info(f"Attempting signup for username={user_create.username}, email={user_create.email}")

        user_create.password = hash_password(user_create.password)

        try:
            user = await self.user_repo.create(user_create)
        except UsernameAlreadyExistsException:
            logger.warning(f"Signup failed: username '{user_create.username}' already exists")
            raise
        except EmailAlreadyExistsException:
            logger.warning(f"Signup failed: email '{user_create.email}' already exists")
            raise

        logger.info(f"User created successfully with id={user.id}")
        return user


    async def login(self, username: str, password: str) -> UserRead:
        logger.info(f"Login attempt for username={username}")

        user = await self.user_repo.get_internal_by_username(username)
        if not user:
            logger.warning(f"Login failed: user '{username}' not found")
            raise LoginFailedException("Invalid username or password.")

        if not verify_password(password, user.password):
            logger.warning(f"Login failed: incorrect password for user '{username}'")
            raise LoginFailedException("Invalid username or password.")

        logger.info(f"User '{username}' logged in successfully")
        return user


    async def update_user(self, user_id: int, user_update: UserUpdate) -> UserRead:
        logger.info(f"Updating user id={user_id}")

        if user_update.password:
            user_update.password = hash_password(user_update.password)

        try:
            updated_user = await self.user_repo.update(user_id, user_update)
        except UsernameAlreadyExistsException:
            logger.warning(f"Update failed: username already exists (user id={user_id})")
            raise
        except EmailAlreadyExistsException:
            logger.warning(f"Update failed: email already exists (user id={user_id})")
            raise
        except NotFoundException:
            logger.error(f"Update failed: user id={user_id} not found")
            raise UserNotFoundException(f"User with id={user_id} not found.")

        logger.info(f"User id={user_id} updated successfully")
        return updated_user


    async def delete_user(self, user_id: int) -> None:
        logger.info(f"Deleting user id={user_id}")
        try:
            await self.user_repo.delete(user_id)
        except NotFoundException:
            logger.error(f"Delete failed: user id={user_id} not found")
            raise UserNotFoundException(f"User with id={user_id} not found.")
        logger.info(f"User id={user_id} deleted successfully")


    async def promote_to_admin(self, user_id: int) -> UserRead:
        logger.info(f"Promoting user id={user_id} to admin")
        try:
            updated_user = await self.user_repo.update(user_id, UserUpdate(role=UserRole.ADMIN))
        except NotFoundException:
            logger.error(f"Promotion failed: user id={user_id} not found")
            raise UserNotFoundException(f"User with id={user_id} not found.")
        logger.info(f"User id={user_id} promoted to admin successfully")
        return updated_user


    async def demote_to_user(self, user_id: int) -> UserRead:
        logger.info(f"Demoting user id={user_id} to regular user")
        try:
            updated_user = await self.user_repo.update(user_id, UserUpdate(role=UserRole.USER))
        except NotFoundException:
            logger.error(f"Demotion failed: user id={user_id} not found")
            raise UserNotFoundException(f"User with id={user_id} not found.")
        logger.info(f"User id={user_id} demoted to regular user successfully")
        return updated_user
