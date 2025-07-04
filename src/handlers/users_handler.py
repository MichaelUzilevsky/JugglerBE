from typing import Optional, List

from src import logger
from src.db.icrud import ICrud
from src.exceptions.users_exceptions.login_failed_exeption import LoginFailedException
from src.exceptions.users_exceptions.username_already_exists_exception import UsernameAlreadyExistsException
from src.models.users.user import User
from src.models.users.user_login import UserLogin
from src.models.users.user_role import UserRole


class UsersHandler:
    def __init__(self, crud: ICrud[User]):
        self._crud = crud

    async def get_user(self, login: UserLogin) -> Optional[User]:
        user =  await self._crud.get({"username": login.username})
        if user:
            logger.info(f"[UsersHandler] Retrieved user with username '{login.username}'")
        else:
            logger.warning(f"[UsersHandler] User with username '{login.username}' not found")
        return user

    async def get_all(self) -> List[User]:
        users =  await self._crud.get_all()
        if users:
            logger.info(f"[UsersHandler] Retrieved {len(users)} user(s) from the system")
        else:
            logger.warning("[UsersHandler] No users found in the system")
        return users

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        user = await self._crud.get({"id": user_id})
        if user:
            logger.info(f"[UsersHandler] Retrieved user with user id '{user_id}'")
        else:
            logger.warning(f"[UsersHandler] User with user id '{user_id}' not found")
        return user

    async def login(self, login: UserLogin) -> Optional[User]:
        user = await self.get_user(login)
        if user and user.password == login.password:
            logger.info(f"[UsersHandler] User '{login.username}' logged in successfully")
            return user

        logger.warning(f"[UsersHandler] Failed login attempt for username '{login.username}'")
        raise LoginFailedException(f"Could not login with the provided credentials")

    async def sign_up(self, user: User) -> Optional[User]:
        existing = await self._crud.get({"username": user.username})
        if existing:
            logger.warning(f"[UsersHandler] Sign-up failed: username '{user.username}' already exists")
            raise UsernameAlreadyExistsException(f"Username '{user.username}' already exists")

        created_user = await self._crud.create(user)
        logger.info(f"[UsersHandler] User '{user.username}' signed up successfully")
        return created_user

    async def delete(self, user_id: str) -> bool:
        result = await self._crud.delete({"id": user_id})
        if result:
            logger.info(f"[UsersHandler] User '{user_id}' deleted successfully")
        else:
            logger.warning(f"[UsersHandler] Failed to delete user '{user_id}'")
        return result

    async def update(self, user: User) -> bool:
        result = await self._crud.update({"id": user.id}, user)
        if result:
            logger.info(f"[UsersHandler] User '{user.username}' updated successfully")
        else:
            logger.warning(f"[UsersHandler] Failed to update user '{user.username}'")
        return result

    async def is_admin(self, user_id: str) -> bool:
        user = await self.get_user_by_id(user_id)
        if user:
            is_admin = user.role == UserRole.ADMIN
            logger.info(f"[UsersHandler] User '{user.username}' is {'an admin' if is_admin else 'not an admin'}")
            return is_admin
        logger.warning(f"[UsersHandler] User id '{user_id}' not found when checking admin status")
        return False

    async def set_admin(self, user_id: str) -> bool:
        user = await self.get_user_by_id(user_id)
        if not user:
            logger.warning(f"[UsersHandler] Cannot set admin: user id '{user_id}' not found")
            return False

        user.role = UserRole.ADMIN
        result = await self.update(user)
        if result:
            logger.info(f"[UsersHandler] User '{user.username}' set as admin successfully")
        else:
            logger.warning(f"[UsersHandler] Failed to update user '{user.username}' to admin")
        return result
