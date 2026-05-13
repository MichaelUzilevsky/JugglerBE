from typing import List

from fastapi import Depends, HTTPException
from starlette import status

from app import logger
from app.api.dependencies.services.users import get_user_service
from app.api.security.jwt_access import get_current_username
from app.domain.schemas.user.enums.user_role import UserRole
from app.domain.schemas.user.user import UserRead
from app.domain.services.user_service import UserService


async def get_current_user(
        username: str = Depends(get_current_username),
        user_service: UserService = Depends(get_user_service)
) -> UserRead:
    user = await user_service.get_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found. Must be logged in")
    return user


def require_roles(roles: List[UserRole]):
    async def dependency(user: UserRead = Depends(get_current_user)):
        if user.role not in roles:
            logger.warning(f"User with user_id='{user.id}' tried accessing {[role.value for role in roles]} "
                           f"only route while his route is '{user.role.value}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: requires {roles}, you are {user.role}",
            )
        return user

    return dependency


admin_only = require_roles([UserRole.ADMIN])
logged_in_only = require_roles([UserRole.USER, UserRole.ADMIN])
