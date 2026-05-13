from typing import List, Optional

from app import logger
from app.domain.repositories.iteam_repository import ITeamRepository
from app.domain.repositories.iuser_repository import IUserRepository
from app.domain.schemas.order.enums.order_purpose import OrderPurpose
from app.domain.schemas.team.team import TeamCreate, TeamRead, TeamUpdate, TeamReadWithMembers
from app.domain.schemas.user.enums.user_role import UserRole
from app.domain.schemas.user.user import UserUpdate
from app.exceptions.teams_exceptions.teams_exceptions import TeamNotFoundException, TeamPermissionDeniedException
from app.exceptions.users_exceptions.users_exceptions import UserNotFoundException


class TeamService:
    def __init__(self, team_repo: ITeamRepository, user_repo: IUserRepository):
        self.team_repo = team_repo
        self.user_repo = user_repo

    async def create_team(self, team_create: TeamCreate) -> TeamRead:
        logger.info(f"Creating team '{team_create.name}'", extra={"event": "team_create_attempt", "team_name": team_create.name})
        team = await self.team_repo.create(team_create)
        logger.info(f"Team '{team.name}' created successfully", extra={"event": "team_create_success", "team_id": team.id})
        return team

    async def get_team(self, team_id: int) -> TeamReadWithMembers:
        team = await self.team_repo.get(team_id)
        if not team:
            raise TeamNotFoundException()

        # Fetch all users to filter members of this team
        all_users = await self.user_repo.list()
        members = [u for u in all_users if u.team_id == team_id]

        team_dict = team.model_dump()
        return TeamReadWithMembers(**team_dict, users=members)

    async def list_teams(self) -> List[TeamRead]:
        teams = await self.team_repo.list()
        logger.info(f"Fetched {len(teams)} teams", extra={"event": "team_list_success", "count": len(teams)})
        return teams

    async def update_team(self, team_id: int, team_update: TeamUpdate) -> TeamRead:
        team = await self.team_repo.update(team_id, team_update)
        if not team:
            raise TeamNotFoundException()
        logger.info(f"Team {team_id} updated", extra={"event": "team_update_success", "team_id": team_id})
        return team

    async def delete_team(self, team_id: int) -> None:
        deleted = await self.team_repo.delete(team_id)
        if not deleted:
            raise TeamNotFoundException()
        logger.info(f"Team {team_id} deleted", extra={"event": "team_delete_success", "team_id": team_id})

    async def add_permission(self, team_id: int, purpose: OrderPurpose) -> bool:
        logger.info(f"Adding permission {purpose.value} to team {team_id}", extra={"event": "team_add_permission_attempt", "team_id": team_id, "purpose": purpose.value})
        return await self.team_repo.add_permission(team_id, purpose)

    async def remove_permission(self, team_id: int, purpose: OrderPurpose) -> bool:
        logger.info(f"Removing permission {purpose.value} from team {team_id}", extra={"event": "team_remove_permission_attempt", "team_id": team_id, "purpose": purpose.value})
        return await self.team_repo.remove_permission(team_id, purpose)

    async def assign_user_to_team(self, user_id: int, team_id: Optional[int]) -> None:
        if team_id is not None:
            team = await self.team_repo.get(team_id)
            if not team:
                raise TeamNotFoundException()

        user = await self.user_repo.update(user_id, UserUpdate(team_id=team_id))
        if not user:
            raise UserNotFoundException()
        logger.info(f"User {user_id} assigned to team {team_id}", extra={"event": "team_assign_user_success", "user_id": user_id, "team_id": team_id})

    async def check_team_permission(self, user_id: int, purpose: OrderPurpose) -> bool:
        """
        Validates if a user's team has permission to create orders for a specific purpose.
        Admins automatically bypass this restriction.
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise UserNotFoundException()

        if user.role == UserRole.ADMIN:
            return True

        if user.team_id is None:
            logger.warning(f"Permission denied: User {user_id} does not belong to any team", extra={"event": "team_permission_denied", "reason": "no_team", "user_id": user_id})
            raise TeamPermissionDeniedException("User does not belong to any team. Only team members can create orders.")

        purposes = await self.team_repo.get_team_purposes(user.team_id)
        if purpose not in purposes:
            logger.warning(f"Permission denied: Team {user.team_id} lacks permission for {purpose.value}", extra={"event": "team_permission_denied", "reason": "purpose_not_allowed", "user_id": user_id, "team_id": user.team_id, "purpose": purpose.value})
            raise TeamPermissionDeniedException(f"Your team does not have permission to create orders for purpose: {purpose.value}")

        return True
