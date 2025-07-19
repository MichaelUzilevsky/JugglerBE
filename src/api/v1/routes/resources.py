from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.resources import get_resources_handler
from src.exceptions.orders_exceptions.resource_not_found_exception import ResourceNotFoundException
from src.exceptions.resources_exceptions.duplicate_resource_name_exception import DuplicateResourceNameException
from src.handlers.resources_handler import ResourcesHandler
from src.models.resources.abstact.base_resource import BaseResource

router = APIRouter(prefix="/resources", tags=["Resources"])


def serialize_resource(resource: BaseResource) -> Dict:
    data = resource.model_dump()
    return data


def resolve_property_type(prop: dict, definitions: dict) -> Dict[str, Any]:
    """
    Resolve a property's type and enum values (if any), including $ref resolution.
    """
    if "$ref" in prop:
        ref_path = prop["$ref"].split("/")[-1]
        ref_def = definitions.get(ref_path)
        if not ref_def:
            return {"type": "string"}
        return {
            "type": ref_def.get("type", "string"),
            "enum": ref_def.get("enum"),
            "title": ref_def.get("title", ref_path)
        }

    if "anyOf" in prop:
        # Handle nullable types
        non_null = [item for item in prop["anyOf"] if item.get("type") != "null"]
        if non_null:
            return {"type": non_null[0].get("type", "string")}

    return {
        "type": prop.get("type", "string"),
        "enum": prop.get("enum"),
        "title": prop.get("title")
    }


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


@router.get("/schemas", response_model=Dict[str, Any])
async def get_forms_metadata(
        handler: ResourcesHandler = Depends(get_resources_handler),
        _=Depends(get_current_user)
):
    metadata = {}

    for cls in handler.resource_classes:
        schema = cls.model_json_schema()
        props = schema.get("properties", {})
        defs = schema.get("$defs", {})
        required = set(schema.get("required", []))

        fields: List[Dict[str, Any]] = []

        for name, prop in props.items():
            resolved = resolve_property_type(prop, defs)

            fields.append({
                "name": name,
                "type": resolved["type"],
                "title": resolved.get("title", name),
                "required": name in required,
                "enum": resolved.get("enum")
            })

        metadata[cls.__name__] = {"fields": fields}

    return metadata


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
