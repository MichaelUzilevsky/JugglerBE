from fastapi import Depends

from app.api.dependencies.repositories.team import get_team_repo
from app.api.dependencies.repositories.users import get_user_repo
from app.domain.repositories.iteam_repository import ITeamRepository
from app.domain.repositories.iuser_repository import IUserRepository
from app.domain.services.team_service import TeamService


async def get_team_service(
        team_repo: ITeamRepository = Depends(get_team_repo),
        user_repo: IUserRepository = Depends(get_user_repo),
) -> TeamService:
    return TeamService(team_repo, user_repo)
