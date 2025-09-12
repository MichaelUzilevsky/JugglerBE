from typing import List, Union

from app.domain.repositories.iresource_repository import IResourceRepository
from app.domain.schemas.resource.enums.resource_type import ResourceType
from app.exceptions.orders_exceptions.resource_not_found_exception import ResourceNotFoundException
from app.exceptions.resources_exceptions.resource_already_exists_exception import ResourceAlreadyExistsException
from app.infrastructure.exceptions.exceptions import RepositoryException, NotFoundException
from app.infrastructure.mappers.sqlalchemy.resource_mapper import ResourceReadSchema, ResourceCreateSchema, \
    ResourceUpdateSchema


class ResourceService:
    """
    Application service layer for Resource management.
    Orchestrates repository calls and applies business rules.
    """

    def __init__(self, resource_repo: IResourceRepository):
        self.repo = resource_repo

    async def list(self) -> List[ResourceReadSchema]:
        return await self.repo.list()

    async def get(self, resource_id: int) -> ResourceReadSchema:
        resource = await self.repo.get(resource_id)
        if not resource:
            raise ResourceNotFoundException(f"Resource with id={resource_id} not found")
        return resource

    async def list_by_type(self, resource_type: ResourceType) -> List[ResourceReadSchema]:
        return await self.repo.list_by_type(resource_type)

    async def get_supported_types(self) -> List[str]:
        return await self.repo.get_supported_types()

    async def get_with_latest_state(self, resource_id: int) -> ResourceReadSchema:
        resource = await self.repo.get_with_latest_state(resource_id)
        if not resource:
            raise ResourceNotFoundException(f"Resource with id={resource_id} not found")
        return resource

    async def list_with_latest_state(self) -> List[ResourceReadSchema]:
        return await self.repo.list_with_latest_state()

    async def create(self, resource: ResourceCreateSchema) -> ResourceReadSchema:
        try:
            return await self.repo.create(resource)
        except ResourceAlreadyExistsException:
            raise
        except RepositoryException as e:
            raise e

    async def update(self, resource_id: int, update: ResourceUpdateSchema) -> ResourceReadSchema:
        try:
            updated = await self.repo.update(resource_id, update)
            if not updated:
                raise ResourceNotFoundException(f"Resource with id={resource_id} not found")
            return updated
        except ResourceAlreadyExistsException:
            raise
        except NotFoundException:
            raise ResourceNotFoundException(f"Resource with id={resource_id} not found")

    async def delete(self, resource_id: int) -> None:
        try:
            deleted = await self.repo.delete(resource_id)
            if not deleted:
                raise ResourceNotFoundException(f"Resource with id={resource_id} not found")
        except NotFoundException:
            raise ResourceNotFoundException(f"Resource with id={resource_id} not found")
