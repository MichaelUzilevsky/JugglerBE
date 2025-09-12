from fastapi import Depends, HTTPException

from app import logger
from app.api.auth.jwt_auth import get_current_username
from app.api.dependencies.services.users import get_user_service
from app.domain.schemas.user.enums.user_role import UserRole
from app.domain.schemas.user.user import UserRead
from app.domain.services.user_service import UserService


async def get_current_user(
        username: str = Depends(get_current_username),
        user_service: UserService = Depends(get_user_service)
) -> UserRead:
    user = await user_service.get_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_admin(
        user: UserRead = Depends(get_current_user),
) -> UserRead:
    if not user.role == UserRole.ADMIN:
        logger.warning(f"User with user_id='{user.id}' tried accessing an admin only route")
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
