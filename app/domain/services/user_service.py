from typing import Optional, List

from app import logger
from app.domain.repositories.iuser_repository import IUserRepository
from app.domain.schemas.user.enums.user_role import UserRole
from app.domain.schemas.user.user import UserCreate, UserRead, UserUpdate
from app.exceptions.users_exceptions.users_exceptions import UsernameAlreadyExistsException, \
    EmailAlreadyExistsException, LoginFailedException, UserNotFoundException
from app.utils.password_security import hash_password, verify_password


class UserService:
    """
    Service layer for user operations.
    Handles business logic, password hashing, validation, role changes,
    and logs all important actions using both standard and security loggers.
    """

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def get_by_username(self, username: str) -> Optional[UserRead]:
        return await self.user_repo.get_by_username(username)

    async def list_users(self) -> List[UserRead]:
        users = await self.user_repo.list()
        logger.info("list_users_success", extra={"count": len(users), "description": f"Fetched {len(users)} users."})
        return users

    async def signup(self, user_create: UserCreate) -> UserRead:
        user_create.password = hash_password(user_create.password)
        logger.info("signup_attempt", extra={"username": user_create.username, "email": user_create.email})

        try:
            user = await self.user_repo.create(user_create)
        except UsernameAlreadyExistsException:
            logger.warning("signup_failed_username", extra={"username": user_create.username})
            raise
        except EmailAlreadyExistsException:
            logger.warning("signup_failed_email", extra={"email": user_create.email})
            raise

        logger.info("user_created", extra={"username": user_create.username, "user_id": user.id})
        return user

    async def login(self, username: str, password: str) -> UserRead:
        logger.info("login_attempt", extra={"username": username})

        user = await self.user_repo.get_internal_by_username(username)
        if not user:
            logger.warning("login_failed_not_found", extra={"username": username})
            raise LoginFailedException("Invalid username or password.")

        if not verify_password(password, user.password):
            logger.warning("login_failed_wrong_password", extra={"username": username})
            raise LoginFailedException("Invalid username or password.")

        logger.info("login_success", extra={"username": username, "user_id": user.id})
        return user

    async def update_user(self, user_id: int, user_update: UserUpdate) -> UserRead:
        if user_update.password:
            user_update.password = hash_password(user_update.password)

        try:
            updated_user = await self.user_repo.update(user_id, user_update)
        except (UsernameAlreadyExistsException, EmailAlreadyExistsException) as e:
            logger.error("update_failed_integrity", extra={"user_id": user_id, "error": str(e)})
            raise
        except UserNotFoundException:
            logger.error("update_failed_not_found", extra={"user_id": user_id})
            raise

        logger.info("user_updated", extra={"user_id": user_id})
        return updated_user

    async def delete_user(self, user_id: int) -> None:
        try:
            await self.user_repo.delete(user_id)
        except UserNotFoundException:
            logger.error("delete_failed_not_found", extra={"user_id": user_id})
            raise

        logger.info("user_deleted", extra={"user_id": user_id})

    async def promote_to_admin(self, user_id: int):
        try:
            updated_user = await self.user_repo.update(user_id, UserUpdate(role=UserRole.ADMIN))
        except UserNotFoundException:
            logger.error("promotion_failed_not_found", extra={"user_id": user_id})
            raise

        logger.info("user_promoted", extra={"user_id": user_id})
        return updated_user

    async def demote_to_user(self, user_id: int):
        try:
            updated_user = await self.user_repo.update(user_id, UserUpdate(role=UserRole.USER))
        except UserNotFoundException:
            logger.error("demotion_failed_not_found", extra={"user_id": user_id})
            raise

        logger.info("user_demoted", extra={"user_id": user_id})
        return updated_user
