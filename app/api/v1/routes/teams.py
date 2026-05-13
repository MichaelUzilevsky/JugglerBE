from typing import List, Optional

from pydantic import BaseModel
from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse

from app.api.dependencies.auth import admin_only, UserRead
from app.api.dependencies.services.team import get_team_service
from app.domain.schemas.order.enums.order_purpose import OrderPurpose
from app.domain.schemas.team.team import TeamCreate, TeamRead, TeamUpdate, TeamReadWithMembers
from app.domain.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["Teams"])


class PermissionAddRequest(BaseModel):
    purpose: OrderPurpose


@router.post("/", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
async def create_team(
        team_create: TeamCreate,
        team_service: TeamService = Depends(get_team_service),
        _: UserRead = Depends(admin_only),
):
    return await team_service.create_team(team_create)


@router.get("/", response_model=List[TeamRead])
async def list_teams(
        team_service: TeamService = Depends(get_team_service),
        _: UserRead = Depends(admin_only),
):
    return await team_service.list_teams()


@router.get("/{team_id}", response_model=TeamReadWithMembers)
async def get_team(
        team_id: int,
        team_service: TeamService = Depends(get_team_service),
        _: UserRead = Depends(admin_only),
):
    return await team_service.get_team(team_id)


@router.patch("/{team_id}", response_model=TeamRead)
async def update_team(
        team_id: int,
        team_update: TeamUpdate,
        team_service: TeamService = Depends(get_team_service),
        _: UserRead = Depends(admin_only),
):
    return await team_service.update_team(team_id, team_update)


@router.delete("/{team_id}", status_code=status.HTTP_200_OK)
async def delete_team(
        team_id: int,
        team_service: TeamService = Depends(get_team_service),
        _: UserRead = Depends(admin_only),
):
    await team_service.delete_team(team_id)
    return JSONResponse(status_code=200, content={"detail": f"Team {team_id} deleted"})


@router.post("/{team_id}/permissions", status_code=status.HTTP_200_OK)
async def add_permission(
        team_id: int,
        req: PermissionAddRequest,
        team_service: TeamService = Depends(get_team_service),
        _: UserRead = Depends(admin_only),
):
    await team_service.add_permission(team_id, req.purpose)
    return {"detail": f"Permission {req.purpose.value} added to team {team_id}"}


@router.delete("/{team_id}/permissions/{purpose}", status_code=status.HTTP_200_OK)
async def remove_permission(
        team_id: int,
        purpose: OrderPurpose,
        team_service: TeamService = Depends(get_team_service),
        _: UserRead = Depends(admin_only),
):
    await team_service.remove_permission(team_id, purpose)
    return {"detail": f"Permission {purpose.value} removed from team {team_id}"}


@router.patch("/{team_id}/members/{user_id}", status_code=status.HTTP_200_OK)
async def assign_user_to_team(
        team_id: int,
        user_id: int,
        team_service: TeamService = Depends(get_team_service),
        _: UserRead = Depends(admin_only),
):
    await team_service.assign_user_to_team(user_id, team_id)
    return {"detail": f"User {user_id} assigned to team {team_id}"}


@router.delete("/members/{user_id}", status_code=status.HTTP_200_OK)
async def unassign_user_from_team(
        user_id: int,
        team_service: TeamService = Depends(get_team_service),
        _: UserRead = Depends(admin_only),
):
    await team_service.assign_user_to_team(user_id, None)
    return {"detail": f"User {user_id} unassigned from any team"}
