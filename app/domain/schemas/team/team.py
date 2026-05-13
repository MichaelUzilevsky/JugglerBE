from __future__ import annotations

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel

from app.domain.schemas.order.enums.order_purpose import OrderPurpose

from app.domain.schemas.user.user import UserRead


# ----------------- Create -----------------
class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    allowed_purposes: List[OrderPurpose] = []


# ----------------- Update -----------------
class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# ----------------- Read -----------------
class TeamPermissionRead(BaseModel):
    id: int
    order_purpose: OrderPurpose

    model_config = {"from_attributes": True}


class TeamRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    permissions: List[TeamPermissionRead] = []

    model_config = {"from_attributes": True}


class TeamReadWithMembers(TeamRead):
    users: List[UserRead] = []
