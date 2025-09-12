from typing import List
from fastapi import APIRouter, Depends, status, HTTPException

from app.api.dependencies.auth import require_admin
from app.api.dependencies.services.resources import get_resource_service
from app.domain.schemas.resource.enums.resource_type import ResourceType
from app.domain.services.resource_service import ResourceService
from app.exceptions.resources_exceptions.resource_already_exists_exception import ResourceAlreadyExistsException
from app.exceptions.orders_exceptions.resource_not_found_exception import ResourceNotFoundException
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
    _ = Depends(require_admin)
):
    try:
        return await service.create(resource)
    except ResourceAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch("/{resource_id}", response_model=ResourceReadSchema)
async def update_resource(
    resource_id: int,
    update: ResourceUpdateSchema,
    service: ResourceService = Depends(get_resource_service),
    _ = Depends(require_admin)
):
    try:
        return await service.update(resource_id, update)
    except ResourceAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: int,
    service: ResourceService = Depends(get_resource_service),
    _ = Depends(require_admin)
):
    try:
        await service.delete(resource_id)
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{resource_id}/latest", response_model=ResourceReadSchema)
async def get_with_latest_state(resource_id: int, service: ResourceService = Depends(get_resource_service)):
    try:
        return await service.get_with_latest_state(resource_id)
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/latest", response_model=List[ResourceReadSchema])
async def list_with_latest_state(service: ResourceService = Depends(get_resource_service)):
    return await service.list_with_latest_state()
