from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.domain.schemas.resource.enums.resource_state import ResourceState
from app.domain.schemas.resource.enums.resource_type import ResourceType
from app.domain.schemas.resource.enums.rt_locations import RtLocations

# ---------- History ----------
class ResourceStateHistoryRead(BaseModel):
    id: int
    old_state: Optional[ResourceState]
    new_state: ResourceState
    description: Optional[str]
    changed_by: Optional[int]

    model_config = {"from_attributes": True}

# ----------------- Base -----------------
class ResourceBase(BaseModel):
    name: str
    resource_state: ResourceState

# ----------------- Create -----------------
class ResourceCreate(ResourceBase):
    description: Optional[str] = None

class RtCreate(ResourceCreate):
    location: RtLocations

class StationCreate(ResourceCreate):
    version: str

class CrawlerRouteCreate(ResourceCreate):
    pass

class PandemicRouteCreate(ResourceCreate):
    pass

# ----------------- Update -----------------
class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    resource_state: Optional[ResourceState] = None
    description: Optional[str] = None

class RtUpdate(ResourceUpdate):
    location: Optional[RtLocations] = None

class StationUpdate(ResourceUpdate):
    version: Optional[str] = None

class CrawlerRouteUpdate(ResourceUpdate):
    pass

class PandemicRouteUpdate(ResourceUpdate):
    pass

# ----------------- Read -----------------
class ResourceRead(ResourceBase):
    id: int
    resource_type: ResourceType
    created_at: datetime
    updated_at: datetime
    state_history: List[ResourceStateHistoryRead] = []

    model_config = {"from_attributes": True}

class RtRead(ResourceRead):
    location: RtLocations

class StationRead(ResourceRead):
    version: str

class CrawlerRouteRead(ResourceRead):
    pass

class PandemicRouteRead(ResourceRead):
    pass
