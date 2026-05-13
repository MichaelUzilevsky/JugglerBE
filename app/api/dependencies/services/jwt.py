from fastapi import Depends

from app.api.dependencies.repositories.jwt import get_jwt_repo
from app.domain.repositories.ijwt_token_repository import IJwtTokenRepository
from app.domain.services.jwt_service import JWTService


async def get_jwt_service(jwt_repo: IJwtTokenRepository = Depends(get_jwt_repo)) -> JWTService:
    return JWTService(jwt_repo)
