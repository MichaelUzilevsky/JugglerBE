from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

from app.domain.schemas.resource.enums.resource_environment import ResourceEnvironment
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

class RemoteResourceCreate(ResourceCreate):
    environment: ResourceEnvironment

class RtCreate(ResourceCreate):
    location: RtLocations

class StationCreate(RemoteResourceCreate):
    version: str

class CrawlerRouteCreate(RemoteResourceCreate):
    horizon_route: int

class PandemicRouteCreate(RemoteResourceCreate):
    pass

# ----------------- Update -----------------
class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    resource_state: Optional[ResourceState] = None
    description: Optional[str] = None

class RemoteResourceUpdate(ResourceUpdate):
    environment: ResourceEnvironment = None

class RtUpdate(ResourceUpdate):
    location: Optional[RtLocations] = None

class StationUpdate(RemoteResourceUpdate):
    version: Optional[str] = None

class CrawlerRouteUpdate(RemoteResourceUpdate):
    horizon_route: int = None

class PandemicRouteUpdate(RemoteResourceUpdate):
    pass

# ----------------- Read -----------------
class ResourceRead(ResourceBase):
    id: int
    resource_type: ResourceType
    created_at: datetime
    updated_at: datetime
    state_history: List[ResourceStateHistoryRead] = []

    model_config = {"from_attributes": True}

class RemoteResourceRead(ResourceRead):
    environment: ResourceEnvironment

class RtRead(ResourceRead):
    resource_type: Literal[ResourceType.RT] = ResourceType.RT
    location: RtLocations

class StationRead(RemoteResourceRead):
    resource_type: Literal[ResourceType.STATION] = ResourceType.STATION
    version: str

class CrawlerRouteRead(RemoteResourceRead):
    resource_type: Literal[ResourceType.CRAWLER_ROUTE] = ResourceType.CRAWLER_ROUTE
    horizon_route: int

class PandemicRouteRead(RemoteResourceRead):
    resource_type: Literal[ResourceType.PANDEMIC_ROUTE] = ResourceType.PANDEMIC_ROUTE
