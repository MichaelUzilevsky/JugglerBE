from fastapi import Depends

from app.api.dependencies.repositories.orders import get_order_repo
from app.api.dependencies.services.resources import get_resource_service
from app.api.dependencies.services.team import get_team_service
from app.api.dependencies.services.users import get_user_service
from app.domain.repositories.iorder_repository import IOrderRepository
from app.domain.services.order_service import OrderService
from app.domain.services.resource_service import ResourceService
from app.domain.services.team_service import TeamService
from app.domain.services.user_service import UserService


async def get_order_service(
        order_repo: IOrderRepository = Depends(get_order_repo),
        user_service: UserService = Depends(get_user_service),
        resource_service: ResourceService = Depends(get_resource_service),
        team_service: TeamService = Depends(get_team_service),
) -> OrderService:
    return OrderService(order_repo, user_service, resource_service, team_service)
