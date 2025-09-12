from typing import List, Optional
from abc import ABC, abstractmethod

from app.infrastructure.mappers.sqlalchemy.resource_mapper import ResourceReadSchema, ResourceCreateSchema, \
    ResourceUpdateSchema


class IResourceRepository(ABC):
    @abstractmethod
    async def create(self, resource_create: ResourceCreateSchema) -> ResourceReadSchema:
        pass

    @abstractmethod
    async def get(self, resource_id: int) -> Optional[ResourceReadSchema]:
        pass

    @abstractmethod
    async def get_with_latest_state(self, obj_id: int) -> Optional[ResourceReadSchema]:
        pass

    @abstractmethod
    async def list_with_latest_state(self) -> List[ResourceReadSchema]:
        pass

    @abstractmethod
    async def list(self) -> List[ResourceReadSchema]:
        pass

    @abstractmethod
    async def list_by_type(self, resource_type: str) -> List[ResourceReadSchema]:
        pass

    @abstractmethod
    async def update(self, resource_id: int, resource_update: ResourceUpdateSchema) -> Optional[ResourceReadSchema]:
        pass

    @abstractmethod
    async def delete(self, resource_id: int) -> bool:
        pass

    @abstractmethod
    async def get_supported_types(self) -> List[str]:
        pass
