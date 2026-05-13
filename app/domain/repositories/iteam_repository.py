from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.schemas.order.enums.order_purpose import OrderPurpose
from app.domain.schemas.team.team import TeamCreate, TeamRead, TeamUpdate


class ITeamRepository(ABC):
    @abstractmethod
    async def create(self, create_schema: TeamCreate) -> TeamRead:
        pass

    @abstractmethod
    async def get(self, team_id: int) -> Optional[TeamRead]:
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[TeamRead]:
        pass

    @abstractmethod
    async def list(self) -> List[TeamRead]:
        pass

    @abstractmethod
    async def update(self, team_id: int, update_schema: TeamUpdate) -> Optional[TeamRead]:
        pass

    @abstractmethod
    async def delete(self, team_id: int) -> bool:
        pass

    @abstractmethod
    async def add_permission(self, team_id: int, purpose: OrderPurpose) -> bool:
        pass

    @abstractmethod
    async def remove_permission(self, team_id: int, purpose: OrderPurpose) -> bool:
        pass

    @abstractmethod
    async def get_team_purposes(self, team_id: int) -> List[OrderPurpose]:
        pass
