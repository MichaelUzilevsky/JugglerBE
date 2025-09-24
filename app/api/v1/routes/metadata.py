from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.domain.schemas.order.enums.order_purpose import ORDER_PURPOSE_DESCRIPTIONS, OrderPurpose
from app.domain.schemas.resource.enums.resource_state import RESOURCE_STATE_DESCRIPTIONS, ResourceState


class StateDescription(BaseModel):
    value: str
    description: str


router = APIRouter(prefix="/metadata", tags=["Metadata"])


@router.get("/resource-states", response_model=List[StateDescription])
async def get_resource_states():
    return [
        {"value": ResourceState(state).value, "description": RESOURCE_STATE_DESCRIPTIONS[state]} for state in
        ResourceState
    ]


@router.get("/order-states", response_model=List[StateDescription])
async def get_resource_states():
    return [
        {"value": OrderPurpose(state).value, "description": ORDER_PURPOSE_DESCRIPTIONS[state]} for state in OrderPurpose
    ]
