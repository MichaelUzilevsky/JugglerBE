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
        logger.info(
            f"Fetched {len(users)} users",
            extra={"event": "user_list_success", "count": len(users)}
        )
        return users

    async def signup(self, user_create: UserCreate) -> UserRead:
        user_create.password = hash_password(user_create.password)
        logger.info(
            f"Signup attempt for username='{user_create.username}'",
            extra={"event": "user_signup_attempt", "username": user_create.username, "email": user_create.email}
        )

        try:
            user = await self.user_repo.create(user_create)
        except UsernameAlreadyExistsException:
            logger.warning(
                f"Signup failed: username '{user_create.username}' already exists",
                extra={"event": "user_signup_failed", "reason": "username_taken", "username": user_create.username}
            )
            raise
        except EmailAlreadyExistsException:
            logger.warning(
                f"Signup failed: email '{user_create.email}' already exists",
                extra={"event": "user_signup_failed", "reason": "email_taken", "email": user_create.email}
            )
            raise

        logger.info(
            f"User '{user_create.username}' created",
            extra={"event": "user_create_success", "user_id": user.id, "username": user_create.username}
        )
        return user

    async def login(self, username: str, password: str) -> UserRead:
        logger.info(
            f"Login attempt for username='{username}'",
            extra={"event": "login_attempt", "username": username}
        )

        user = await self.user_repo.get_internal_by_username(username)
        if not user:
            logger.warning(
                f"Login failed: username '{username}' not found",
                extra={"event": "login_failed", "reason": "user_not_found", "username": username}
            )
            raise LoginFailedException("Invalid username or password.")

        if not verify_password(password, user.password):
            logger.warning(
                f"Login failed: wrong password for username='{username}'",
                extra={"event": "login_failed", "reason": "wrong_password", "username": username}
            )
            raise LoginFailedException("Invalid username or password.")

        logger.info(
            f"Login successful for username='{username}'",
            extra={"event": "login_success", "username": username, "user_id": user.id}
        )
        return user

    async def update_user(self, user_id: int, user_update: UserUpdate) -> UserRead:
        if user_update.password:
            user_update.password = hash_password(user_update.password)

        try:
            updated_user = await self.user_repo.update(user_id, user_update)
        except (UsernameAlreadyExistsException, EmailAlreadyExistsException) as e:
            logger.warning(
                f"User update failed: integrity violation for user_id={user_id}",
                extra={"event": "user_update_failed", "reason": "integrity_violation", "user_id": user_id, "error": str(e)}
            )
            raise
        except UserNotFoundException:
            logger.warning(
                f"User update failed: user_id={user_id} not found",
                extra={"event": "user_update_not_found", "user_id": user_id}
            )
            raise

        logger.info(
            f"User id={user_id} updated",
            extra={"event": "user_update_success", "user_id": user_id}
        )
        return updated_user

    async def delete_user(self, user_id: int, actor_id: int = None) -> None:
        # Fetch before deleting to snapshot the username
        user = await self.user_repo.get(user_id)
        if not user:
            logger.warning(
                f"User delete failed: user_id={user_id} not found",
                extra={"event": "user_delete_not_found", "user_id": user_id, "actor_id": actor_id}
            )
            raise UserNotFoundException(f"User with id={user_id} not found")

        await self.user_repo.delete(user_id)
        logger.info(
            f"User '{user.username}' (id={user_id}) deleted",
            extra={"event": "user_delete_success", "user_id": user_id, "deleted_username": user.username, "actor_id": actor_id}
        )

    async def promote_to_admin(self, user_id: int, actor_id: int = None):
        try:
            updated_user = await self.user_repo.update(user_id, UserUpdate(role=UserRole.ADMIN))
        except UserNotFoundException:
            logger.warning(
                f"Promotion failed: user_id={user_id} not found",
                extra={"event": "user_promote_not_found", "user_id": user_id, "actor_id": actor_id}
            )
            raise

        logger.info(
            f"User id={user_id} promoted to admin",
            extra={"event": "user_promote_success", "user_id": user_id, "actor_id": actor_id}
        )
        return updated_user

    async def demote_to_user(self, user_id: int, actor_id: int = None):
        try:
            updated_user = await self.user_repo.update(user_id, UserUpdate(role=UserRole.USER))
        except UserNotFoundException:
            logger.warning(
                f"Demotion failed: user_id={user_id} not found",
                extra={"event": "user_demote_not_found", "user_id": user_id, "actor_id": actor_id}
            )
            raise

        logger.info(
            f"User id={user_id} demoted to user",
            extra={"event": "user_demote_success", "user_id": user_id, "actor_id": actor_id}
        )
        return updated_user
