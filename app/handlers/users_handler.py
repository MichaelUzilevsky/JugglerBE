from typing import Optional, List

from app import logger
from app.exceptions.users_exceptions.login_failed_exception import LoginFailedException
from app.exceptions.users_exceptions.username_already_exists_exception import UsernameAlreadyExistsException
from app.domain.schemas.user.enums.user_role import UserRole

from app.utils.password_security import verify_password


class UsersHandler:
    def __init__(self, crud: ICrud[User]):
        """
        Initialize UsersHandler with a CRUD instance for User.
        """
        self._crud = crud

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user by their login credentials (username).
        """
        user = await self._crud.get({"username": username})
        if user:
            logger.debug(f"[UsersHandler] Retrieved user with username '{username}'")
        else:
            logger.warning(f"[UsersHandler] User with username '{username}' not found")
        return user

    async def get_all(self) -> List[User]:
        """
        Retrieve all users in the system.
        """
        users = await self._crud.get_all()
        if users:
            logger.debug(f"[UsersHandler] Retrieved {len(users)} user(s) from the system")
        else:
            logger.warning("[UsersHandler] No users found in the system")
        return users

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by their unique user ID.
        """
        user = await self._crud.get({"id": user_id})
        if user:
            logger.debug(f"[UsersHandler] Retrieved user with user id '{user_id}'")
        else:
            logger.warning(f"[UsersHandler] User with user id '{user_id}' not found")
        return user

    async def login(self, login: UserLogin) -> Optional[User]:
        """
        Attempt to log in a user with the provided credentials. Raises on failure.
        """
        user = await self.get_user_by_username(login.username)
        if user:
            if verify_password(login.password, user.password):
                logger.info(f"[UsersHandler] User '{login.username}' logged in successfully")
                return user
            else:
                logger.warning(f"[UsersHandler] Login failed for '{login.username}': incorrect password")
        else:
            logger.warning(f"[UsersHandler] Login failed: username '{login.username}' not found")
        raise LoginFailedException("Invalid username or password")

    async def sign_up(self, user: User) -> Optional[User]:
        """
        Register a new user. Raises if the username already exists.
        """
        existing = await self._crud.get({"username": user.username})
        if existing:
            logger.warning(f"[UsersHandler] Cannot sign up user '{user.username}': username already exists")
            raise UsernameAlreadyExistsException(f"Username '{user.username}' already exists")

        created_user = await self._crud.create(user)
        if created_user:
            logger.info(f"[UsersHandler] New user '{user.username}' signed up successfully with ID '{created_user.id}'")
        else:
            logger.error(f"[UsersHandler] Failed to create user '{user.username}'")
        return created_user

    async def delete(self, user_id: str) -> bool:
        """
        Delete a user by their user ID.
        """
        result = await self._crud.delete({"id": user_id})
        if result:
            logger.info(f"[UsersHandler] Successfully deleted user with ID '{user_id}'")
        else:
            logger.warning(f"[UsersHandler] Failed to delete user: no user found with ID '{user_id}'")
        return result

    async def update(self, user: User) -> bool:
        """
        Update a user's information.
        """
        if not user.id:
            logger.error("[UsersHandler] Cannot update user: missing user ID")
            return False

        existing = await self.get_user_by_id(user.id)
        if not existing:
            logger.warning(f"[UsersHandler] Update failed: no user found with ID '{user.id}'")
            return False

        result = await self._crud.update({"id": user.id}, user)
        if result:
            logger.info(f"[UsersHandler] User '{user.username}' (ID: {user.id}) updated successfully")
        else:
            logger.warning(
                f"[UsersHandler] Failed to update user '{user.username}' (ID: {user.id})")
        return result

    async def is_admin(self, user_id: str) -> bool:
        """
        Check if a user is an admin by their user ID.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            logger.warning(f"[UsersHandler] Admin check failed: no user found with ID '{user_id}'")
            return False

        is_admin = user.role == UserRole.ADMIN
        logger.debug(
            f"[UsersHandler] User '{user.username}' (ID: {user.id}) admin check: {'is admin' if is_admin else 'not admin'}")
        return is_admin

    async def set_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """
        Set a user's role to new given role by their user ID.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            logger.warning(f"[UsersHandler] Cannot set {new_role}: user with ID '{user_id}' not found")
            return False

        user.role = new_role
        result = await self.update(user)
        if result:
            logger.info(f"[UsersHandler] User '{user.username}' (ID: {user.id}) "
                        f"{"promoted to admin" if new_role == UserRole.ADMIN else "demoted to user"}")
        else:
            logger.warning(f"[UsersHandler] Failed to "
                           f"{f"promote user '{user.username}' to admin"
                           if new_role == UserRole.ADMIN else
                           f"demote user '{user.username}' to user"}")
        return result
