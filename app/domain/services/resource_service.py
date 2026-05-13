from typing import List

from app import logger
from app.domain.repositories.iresource_repository import IResourceRepository
from app.domain.schemas.resource.enums.resource_type import ResourceType
from app.exceptions.resources_exceptions.resources_exceptions import ResourceAlreadyExistsException, \
    ResourceNotFoundException
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
        resources = await self.repo.list()
        logger.info(
            f"Fetched {len(resources)} resources",
            extra={"event": "resource_list_success", "count": len(resources)},
        )
        return resources

    async def get(self, resource_id: int) -> ResourceReadSchema:
        try:
            resource = await self.repo.get(resource_id)
            logger.info(
                f"Fetched resource id={resource_id}",
                extra={
                    "event": "resource_get_success",
                    "resource_id": resource_id,
                    "resource_type": getattr(resource, "resource_type", None),
                    "resource_name": getattr(resource, "name", None),
                },
            )
            return resource
        except ResourceNotFoundException:
            logger.warning(
                f"Resource id={resource_id} not found",
                extra={"event": "resource_get_not_found", "resource_id": resource_id},
            )
            raise

    async def list_by_type(self, resource_type: ResourceType) -> List[ResourceReadSchema]:
        resources = await self.repo.list_by_type(resource_type)
        logger.info(
            f"Fetched {len(resources)} resources of type='{resource_type.value}'",
            extra={
                "event": "resource_list_by_type_success",
                "resource_type": resource_type.value,
                "count": len(resources),
            },
        )
        return resources

    async def get_supported_types(self) -> List[str]:
        types = await self.repo.get_supported_types()
        logger.info(
            f"Supported resource types: {[str(t) for t in types]}",
            extra={"event": "resource_get_supported_types", "supported_types": types},
        )
        return types

    async def create(self, resource: ResourceCreateSchema, user_id: int) -> ResourceReadSchema:
        logger.info(
            f"Creating resource '{resource.name}'",
            extra={"event": "resource_create_attempt", "resource_name": resource.name, "actor_id": user_id},
        )
        try:
            created = await self.repo.create(resource, changing_user_id=user_id)
            logger.info(
                f"Resource '{created.name}' created (id={created.id})",
                extra={
                    "event": "resource_create_success",
                    "resource_id": created.id,
                    "resource_name": created.name,
                    "resource_type": created.resource_type,
                    "actor_id": user_id,
                },
            )
            return created

        except ResourceAlreadyExistsException:
            logger.warning(
                f"Resource creation failed: name '{resource.name}' already exists",
                extra={"event": "resource_create_conflict", "resource_name": resource.name, "actor_id": user_id},
            )
            raise

    async def update(self, resource_id: int, update: ResourceUpdateSchema, user_id: int) -> ResourceReadSchema:
        try:
            updated = await self.repo.update(resource_id, update, changing_user_id=user_id)
            logger.info(
                f"Resource id={resource_id} updated",
                extra={"event": "resource_update_success", "resource_id": resource_id, "actor_id": user_id},
            )
            return updated

        except ResourceNotFoundException:
            logger.warning(
                f"Resource update failed: id={resource_id} not found",
                extra={"event": "resource_update_not_found", "resource_id": resource_id, "actor_id": user_id},
            )
            raise

        except ResourceAlreadyExistsException:
            logger.warning(
                f"Resource update failed: duplicate name for id={resource_id}",
                extra={"event": "resource_update_conflict", "resource_id": resource_id, "actor_id": user_id},
            )
            raise

    async def delete(self, resource_id: int, actor_id: int = None) -> None:
        # Fetch before deleting to snapshot the resource name
        try:
            resource = await self.repo.get(resource_id)
        except ResourceNotFoundException:
            logger.warning(
                f"Resource delete failed: id={resource_id} not found",
                extra={"event": "resource_delete_not_found", "resource_id": resource_id, "actor_id": actor_id},
            )
            raise

        await self.repo.delete(resource_id)
        logger.info(
            f"Resource '{resource.name}' (id={resource_id}) deleted",
            extra={
                "event": "resource_delete_success",
                "resource_id": resource_id,
                "deleted_resource_name": resource.name,
                "deleted_resource_type": resource.resource_type,
                "actor_id": actor_id,
            },
        )
