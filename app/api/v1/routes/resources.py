from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.resources import get_resources_handler
from app.exceptions.orders_exceptions.resource_not_found_exception import ResourceNotFoundException
from app.exceptions.resources_exceptions.duplicate_resource_name_exception import DuplicateResourceNameException
from app.handlers.resources_handler import ResourcesHandler
from app.models.resources.abstract.base_resource import BaseResource

router = APIRouter(prefix="/resources", tags=["Resources"])


def serialize_resource(resource: BaseResource) -> Dict:
    data = resource.model_dump()
    return data


@router.get("/", response_model=List[Dict])
async def get_all_resources(
        handler: ResourcesHandler = Depends(get_resources_handler),
        _=Depends(get_current_user)
):
    resources = await handler.get_all()
    return [serialize_resource(r) for r in resources]


@router.get("/by-type", response_model=List[Dict])
async def get_resources_by_type(
        resource_type: str = Query(..., description="Resource class name like 'Rt', 'Station', etc."),
        handler: ResourcesHandler = Depends(get_resources_handler),
        _=Depends(get_current_user)
):
    resource_classes = {cls.__name__: cls for cls in handler.resource_classes}
    resource_class = resource_classes.get(resource_type)

    if not resource_class:
        raise HTTPException(status_code=404, detail=f"Resource type '{resource_type}' not found")

    items = await handler.get_all_by_resource_class(resource_class)
    return [serialize_resource(r) for r in items]


@router.get("/types", response_model=List[str])
async def get_all_resource_types(
        handler: ResourcesHandler = Depends(get_resources_handler),
        _=Depends(get_current_user)
):
    return [cls.__name__ for cls in handler.resource_classes]


@router.post("/create", response_model=Dict, status_code=status.HTTP_201_CREATED)
async def create_resource(
        resource_type: str = Query(..., description="Resource type to create (e.g., 'Rt', 'Station')"),
        handler: ResourcesHandler = Depends(get_resources_handler),
        _=Depends(get_current_user),
        body: dict = None
):
    resource_classes = {cls.__name__: cls for cls in handler.resource_classes}
    cls = resource_classes.get(resource_type)
    if not cls:
        raise HTTPException(status_code=404, detail=f"Resource type '{resource_type}' not found")

    try:
        item = cls(**body)
        created = await handler.create(cls, item)
        return serialize_resource(created)
    except DuplicateResourceNameException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.patch("/update", response_model=Dict)
async def update_resource(
        handler: ResourcesHandler = Depends(get_resources_handler),
        _=Depends(get_current_user),
        body: dict = None
):
    try:
        item_id = body.get("id")
        if not item_id:
            raise HTTPException(status_code=400, detail="Missing 'id' in body")

        _, resource_class = await handler.get_by_id(item_id)
        item = resource_class(**body)
        success = await handler.update(item)

        if not success:
            raise HTTPException(status_code=500, detail="Update failed")

        return serialize_resource(item)
    except DuplicateResourceNameException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
        resource_id: str,
        handler: ResourcesHandler = Depends(get_resources_handler),
        _=Depends(get_current_user)
):
    try:
        deleted = await handler.delete(resource_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Could not delete resource")
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
