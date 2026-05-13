from typing import List

from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse

from app.api.dependencies.auth import admin_only
from app.api.dependencies.services.resources import get_resource_service
from app.domain.schemas.resource.enums.resource_type import ResourceType
from app.domain.schemas.user.user import UserRead
from app.domain.services.resource_service import ResourceService
from app.infrastructure.mappers.sqlalchemy.resource_mapper import ResourceReadSchema, ResourceCreateSchema, \
    ResourceUpdateSchema

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("/", response_model=List[ResourceReadSchema])
async def list_resources(service: ResourceService = Depends(get_resource_service)):
    return await service.list()


@router.get("/types", response_model=List[str])
async def get_supported_types(service: ResourceService = Depends(get_resource_service)):
    return await service.get_supported_types()


@router.get("/type/{resource_type}", response_model=List[ResourceReadSchema])
async def list_by_type(resource_type: ResourceType, service: ResourceService = Depends(get_resource_service)):
    return await service.list_by_type(resource_type)


@router.post("/", response_model=ResourceReadSchema, status_code=status.HTTP_201_CREATED)
async def create_resource(
        resource: ResourceCreateSchema,
        service: ResourceService = Depends(get_resource_service),
        user: UserRead = Depends(admin_only)
):
    return await service.create(resource, user.id)


@router.patch("/{resource_id}", response_model=ResourceReadSchema)
async def update_resource(
        resource_id: int,
        update: ResourceUpdateSchema,
        service: ResourceService = Depends(get_resource_service),
        user: UserRead = Depends(admin_only)
):
    return await service.update(resource_id, update, user.id)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
        resource_id: int,
        service: ResourceService = Depends(get_resource_service),
        admin: UserRead = Depends(admin_only)
):
    await service.delete(resource_id, actor_id=admin.id)
    return JSONResponse(status_code=200, content={"detail": "Resource deleted"})
