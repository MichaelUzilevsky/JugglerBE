from typing import Dict, List, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.dependencies.resources import get_resources_handler
from src.handlers.resources_handler import ResourcesHandler
from src.models.orders.enums.order_purpose import ORDER_PURPOSE_DESCRIPTIONS, OrderPurpose
from src.models.resources.enums.resource_state import RESOURCE_STATE_DESCRIPTIONS, ResourceState

class StateDescription(BaseModel):
    value: str
    description: str

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


router = APIRouter(prefix="/metadata", tags=["Metadata"])

@router.get("/resource-states", response_model=List[StateDescription])
async def get_resource_states():
    return [
        {"value" : ResourceState(state).value, "description": RESOURCE_STATE_DESCRIPTIONS[state]} for state in ResourceState
    ]

@router.get("/order-states", response_model=List[StateDescription])
async def get_resource_states():
    return [
        {"value" : OrderPurpose(state).value, "description": ORDER_PURPOSE_DESCRIPTIONS[state]} for state in OrderPurpose
    ]

@router.get("/resource-schemas", response_model=Dict[str, Any])
async def get_forms_metadata(
        handler: ResourcesHandler = Depends(get_resources_handler)
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

