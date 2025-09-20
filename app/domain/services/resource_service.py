from typing import List

from app import logger
from app.domain.repositories.iresource_repository import IResourceRepository
from app.domain.schemas.resource.enums.resource_type import ResourceType
from app.exceptions.orders_exceptions.resource_not_found_exception import ResourceNotFoundException
from app.exceptions.resources_exceptions.resource_already_exists_exception import ResourceAlreadyExistsException
from app.domain.exceptions.repository_exceptions import RepositoryException, NotFoundException
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

    async def create(self, resource: ResourceCreateSchema, user_id: int) -> ResourceReadSchema:
        logger.info("Attempting to create new resource")
        try:
            created_resource =  await self.repo.create(resource, changing_user_id=user_id)
        except ResourceAlreadyExistsException:
            logger.exception(f"Resource with name='{resource.name}' already exists")
            raise
        except RepositoryException as e:
            logger.exception(str(e))
            raise e

        logger.info(f"Resource created successfully with id='{created_resource.id}'")
        return created_resource

    async def update(self, resource_id: int, update: ResourceUpdateSchema, user_id: int) -> ResourceReadSchema:
        logger.info(f"Attempting to update resource with id='{resource_id}'")
        try:
            updated = await self.repo.update(resource_id, update, changing_user_id=user_id)
            if not updated:
                logger.info(f"Resource with id={resource_id} not found")
                raise ResourceNotFoundException(f"Resource with id={resource_id} not found")
            logger.info(f"Resource with id='{resource_id}' updated successfully")
            return updated
        except ResourceAlreadyExistsException:
            logger.exception(f"Resource with this name already exists")
            raise
        except NotFoundException:
            logger.info(f"Resource with id={resource_id} not found")
            raise ResourceNotFoundException(f"Resource with id={resource_id} not found")

    async def delete(self, resource_id: int) -> None:
        logger.info(f"Attempting to delete resource with id='{resource_id}'")
        try:
            deleted = await self.repo.delete(resource_id)
            if not deleted:
                logger.info(f"Resource with id={resource_id} not found")
                raise ResourceNotFoundException(f"Resource with id={resource_id} not found")
        except NotFoundException:
            logger.info(f"Resource with id={resource_id} not found")
            raise ResourceNotFoundException(f"Resource with id={resource_id} not found")

        logger.info(f"Resource with id='{resource_id}' deleted successfully")
