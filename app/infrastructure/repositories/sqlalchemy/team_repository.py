from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.sqlalchemy.models.team import Team, TeamPermission
from app.domain.exceptions.repository_exceptions import IntegrityViolationException, NotFoundException, \
    RepositoryException
from app.domain.repositories.iteam_repository import ITeamRepository
from app.domain.schemas.order.enums.order_purpose import OrderPurpose
from app.domain.schemas.team.team import TeamCreate, TeamRead, TeamUpdate
from app.exceptions.teams_exceptions.teams_exceptions import TeamAlreadyExistsException, TeamNotFoundException, \
    TeamPermissionAlreadyExistsException, TeamPermissionNotFoundException
from app.infrastructure.mappers.sqlalchemy.team_mapper import TeamMapper
from app.infrastructure.repositories.sqlalchemy.base_repository import SQLAlchemyBaseRepository


class SQLAlchemyTeamRepository(
    SQLAlchemyBaseRepository[TeamRead, TeamCreate, TeamUpdate, Team],
    ITeamRepository,
):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Team, TeamMapper)

    def _default_options(self) -> list:
        return [selectinload(Team.permissions)]

    async def create(self, create_schema: TeamCreate) -> TeamRead:
        try:
            team = await super().create(create_schema)
            self._log_info("team_created", msg=f"Team created with name={create_schema.name}", extra={"team_id": team.id, "team_name": create_schema.name})
            return team
        except IntegrityViolationException:
            raise TeamAlreadyExistsException()

    async def update(self, obj_id: int, update_schema: TeamUpdate) -> Optional[TeamRead]:
        try:
            team = await super().update(obj_id, update_schema)
            self._log_info("team_updated", msg=f"Team updated with id={obj_id}", extra={"team_id": obj_id})
            return team
        except IntegrityViolationException:
            raise TeamAlreadyExistsException()
        except NotFoundException:
            raise TeamNotFoundException()

    async def get_by_name(self, name: str) -> Optional[TeamRead]:
        try:
            stmt = select(Team).where(Team.name == name).options(*self._default_options())
            result = await self.session.execute(stmt)
            orm_team = result.scalar_one_or_none()
            if orm_team:
                return self.mapper.to_read(orm_team)
            return None
        except SQLAlchemyError as e:
            self._log_error("team_get_by_name_error", msg=f"Error fetching team by name={name}", extra={"error": str(e)})
            raise RepositoryException()

    async def add_permission(self, team_id: int, purpose: OrderPurpose) -> bool:
        try:
            # Verify team exists
            team = await self.get(team_id)
            if not team:
                raise TeamNotFoundException()

            perm = TeamPermission(team_id=team_id, order_purpose=purpose)
            self.session.add(perm)
            await self.session.flush()
            self._log_info("team_permission_added", msg=f"Added permission {purpose} to team_id={team_id}", extra={"team_id": team_id, "purpose": purpose.value})
            return True
        except IntegrityViolationException:
            raise TeamPermissionAlreadyExistsException()
        except SQLAlchemyError as e:
            err = str(e).lower()
            if "unique" in err or "duplicate" in err:
                raise TeamPermissionAlreadyExistsException()
            if "foreign key" in err:
                raise TeamNotFoundException()
            self._log_error("team_add_permission_error", extra={"error": str(e)})
            raise RepositoryException()

    async def remove_permission(self, team_id: int, purpose: OrderPurpose) -> bool:
        try:
            stmt = delete(TeamPermission).where(
                TeamPermission.team_id == team_id,
                TeamPermission.order_purpose == purpose
            )
            result = await self.session.execute(stmt)
            await self.session.flush()
            if result.rowcount == 0:
                raise TeamPermissionNotFoundException()
            self._log_info("team_permission_removed", msg=f"Removed permission {purpose} from team_id={team_id}", extra={"team_id": team_id, "purpose": purpose.value})
            return True
        except TeamPermissionNotFoundException:
            raise
        except SQLAlchemyError as e:
            self._log_error("team_remove_permission_error", extra={"error": str(e)})
            raise RepositoryException()

    async def get_team_purposes(self, team_id: int) -> List[OrderPurpose]:
        try:
            stmt = select(TeamPermission.order_purpose).where(TeamPermission.team_id == team_id)
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self._log_error("team_get_purposes_error", extra={"error": str(e)})
            raise RepositoryException()
