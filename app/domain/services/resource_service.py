from typing import List

from app import logger
from app.domain.exceptions.repository_exceptions import RepositoryException
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
        try:
            resources = await self.repo.list()
            logger.info(
                "Fetched resources list",
                extra={"event": "resource_list_success", "count": len(resources)},
            )
            return resources
        except RepositoryException as exc:
            logger.error(
                "DB error while listing resources",
                exc_info=True,
                extra={"event": "resource_list_db_error", "error": str(exc)},
            )
            raise

    async def get(self, resource_id: int) -> ResourceReadSchema:
        try:
            resource = await self.repo.get(resource_id)
            # repo raises ResourceNotFoundException if not found, so if we reach here it's present
            logger.info(
                "Fetched resource",
                extra={
                    "event": "resource_get_success",
                    "resource_id": resource_id,
                    "resource_type": getattr(resource, "resource_type", None),
                    "resource_name": getattr(resource, "name", None),
                },
            )
            return resource
        except ResourceNotFoundException as exc:
            logger.warning(
                "Resource not found",
                extra={"event": "resource_get_not_found", "resource_id": resource_id, "reason": str(exc)},
            )
            raise
        except RepositoryException as exc:
            logger.error(
                "DB error while fetching resource",
                exc_info=True,
                extra={"event": "resource_get_db_error", "resource_id": resource_id, "error": str(exc)},
            )
            raise

    async def list_by_type(self, resource_type: ResourceType) -> List[ResourceReadSchema]:
        try:
            resources = await self.repo.list_by_type(resource_type)
            logger.info(
                "Fetched resources by type",
                extra={
                    "event": "resource_list_by_type_success",
                    "resource_type": resource_type.value,
                    "count": len(resources),
                },
            )
            return resources
        except RepositoryException as exc:
            logger.error(
                "DB error while listing resources by type",
                exc_info=True,
                extra={"event": "resource_list_by_type_db_error", "resource_type": resource_type.value,
                       "error": str(exc)},
            )
            raise

    async def get_supported_types(self) -> List[str]:
        types = await self.repo.get_supported_types()
        logger.info(
            "Supported resource types",
            extra={"event": "resource_get_supported_types", "supported_types": types},
        )
        return types

    async def create(self, resource: ResourceCreateSchema, user_id: int) -> ResourceReadSchema:
        logger.info(
            "Attempting to create resource",
            extra={"event": "resource_create_attempt", "resource_name": resource.name, "user_id": user_id},
        )
        try:
            created = await self.repo.create(resource, changing_user_id=user_id)
            logger.info(
                "Resource created",
                extra={
                    "event": "resource_create_success",
                    "resource_id": getattr(created, "id", None),
                    "resource_name": getattr(created, "name", None),
                    "user_id": user_id,
                },
            )
            return created

        except ResourceAlreadyExistsException as exc:
            logger.warning(
                "Resource creation failed - already exists",
                extra={"event": "resource_create_conflict", "resource_name": resource.name, "user_id": user_id,
                       "reason": str(exc)},
            )
            raise

        except RepositoryException as exc:
            logger.error(
                "DB error while creating resource",
                exc_info=True,
                extra={"event": "resource_create_db_error", "resource_name": resource.name, "user_id": user_id,
                       "error": str(exc)},
            )
            raise

    async def update(self, resource_id: int, update: ResourceUpdateSchema, user_id: int) -> ResourceReadSchema:
        logger.info(
            "Attempting to update resource",
            extra={"event": "resource_update_attempt", "resource_id": resource_id, "user_id": user_id},
        )
        try:
            updated = await self.repo.update(resource_id, update, changing_user_id=user_id)
            logger.info(
                "Resource updated",
                extra={"event": "resource_update_success", "resource_id": resource_id, "user_id": user_id},
            )
            return updated

        except ResourceNotFoundException as exc:
            logger.warning(
                "Resource update failed - not found",
                extra={"event": "resource_update_not_found", "resource_id": resource_id, "user_id": user_id,
                       "reason": str(exc)},
            )
            raise

        except ResourceAlreadyExistsException as exc:
            logger.warning(
                "Resource update failed - conflict (duplicate name)",
                extra={"event": "resource_update_conflict", "resource_id": resource_id, "user_id": user_id,
                       "reason": str(exc)},
            )
            raise

        except RepositoryException as exc:
            logger.error(
                "DB error while updating resource",
                exc_info=True,
                extra={"event": "resource_update_db_error", "resource_id": resource_id, "user_id": user_id,
                       "error": str(exc)},
            )
            raise

    async def delete(self, resource_id: int) -> None:
        logger.info(
            "Attempting to delete resource",
            extra={"event": "resource_delete_attempt", "resource_id": resource_id},
        )
        try:
            await self.repo.delete(resource_id)
            logger.info(
                "Resource deleted",
                extra={"event": "resource_delete_success", "resource_id": resource_id},
            )
        except ResourceNotFoundException as exc:
            logger.warning(
                "Resource delete failed - not found",
                extra={"event": "resource_delete_not_found", "resource_id": resource_id, "reason": str(exc)},
            )
            raise
        except RepositoryException as exc:
            logger.error(
                "DB error while deleting resource",
                exc_info=True,
                extra={"event": "resource_delete_db_error", "resource_id": resource_id, "error": str(exc)},
            )
            raise
