from fastapi import Depends, HTTPException

from src import logger
from src.api.auth.jwt_auth import get_current_user_id
from src.api.dependencies.users import get_users_handler
from src.handlers.users_handler import UsersHandler
from src.models.users.enums.user_role import UserRole
from src.models.users.user import User


async def get_current_user(
        user_id: str = Depends(get_current_user_id),
        handler: UsersHandler = Depends(get_users_handler)
) -> User:
    user = await handler.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_admin(
        user: User = Depends(get_current_user),
) -> User:
    if not user.role == UserRole.ADMIN:
        logger.warning(f"User with user_id='{user.id}' tried accessing an admin only route")
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
