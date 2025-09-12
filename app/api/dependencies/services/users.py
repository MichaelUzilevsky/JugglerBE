from fastapi import Depends
from app.domain.repositories.iuser_repository import IUserRepository
from app.api.dependencies.repositories.users import get_user_repo
from app.domain.services.user_service import UserService


async def get_user_service(user_repo: IUserRepository = Depends(get_user_repo)) -> UserService:
    return UserService(user_repo)
