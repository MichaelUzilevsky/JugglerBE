from typing import Type, TypeVar, List, Dict, Optional, Tuple

from src import config, logger
from src.db.mongodb.mongo_crud import MongoCrud
from src.db.abstract.icrud import ICrud
from src.exceptions.orders_exceptions.resource_not_found_exception import ResourceNotFoundException
from src.exceptions.resources_exceptions.duplicate_resource_name_exception import DuplicateResourceNameException
from src.models.resources.abstact.base_resource import BaseResource
from src.utils.project_resources import ProjectResources

T = TypeVar("T", bound=BaseResource)

class ResourcesHandler:
    def __init__(self, resources_config_data: dict) -> None:
        """
        Initialize ResourcesHandler with a dict of resource names and initialize the cruds.
        """
        self._class_to_crud: Dict[Type[T], ICrud[T]] = {}
        self.resource_classes: List[Type[T]] = ProjectResources.retrieve_project_resources(resources_config_data)
        self._initialize_cruds(self.resource_classes)

    def _initialize_cruds(self, resource_classes: List[Type[T]]) -> None:
        """
        Map each resource class to its corresponding CRUD instance using config.
        """
        for cls in resource_classes:
            collection_key = self._get_collection_key(cls.__name__)
            try:
                collection_name = config.get_value("mongodb", "collections", "resources", collection_key)
                self._class_to_crud[cls] = MongoCrud(cls, collection_name)
                logger.debug(f"[ResourcesHandler] Mapped resource class '{cls.__name__}' "
                             f"to collection '{collection_name}'")
            except KeyError:
                logger.error(f"[ResourcesHandler] Collection config missing for resource class '{cls.__name__}' "
                             f"(expected key: '{collection_key}')")

    def _get_crud(self, resource_type: Type[T]) -> ICrud[T]:
        """
        Retrieve the CRUD instance for a given resource type.
        Raises ValueError if not mapped.
        """
        if resource_type not in self._class_to_crud:
            error_msg = f"[ResourcesHandler] No CRUD instance mapped for resource type: {resource_type.__name__}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        return self._class_to_crud[resource_type]

    @staticmethod
    def _get_collection_key(class_name: str) -> str:
        """
        Convert a class name to a collection key in snake_case and plural form.
        """
        import re
        snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
        return f"{snake_case}s"

    async def create(self, resource_type: Type[T], item: T) -> T:
        """
        Create a new resource of the given type. Raises on duplicate name.
        """
        crud = self._get_crud(resource_type)

        existing = await crud.get({"name": item.name})
        if existing:
            logger.warning(f"[ResourcesHandler] Create failed: resource with name '{item.name}' "
                           f"already exists (id={existing.id})")
            raise DuplicateResourceNameException(item.name)

        created = await crud.create(item)
        if created:
            logger.info(f"[ResourcesHandler] Created {resource_type.__name__} "
                        f"with id={created.id}, name='{item.name}'")
        else:
            logger.error(f"[ResourcesHandler] Failed to create {resource_type.__name__} named '{item.name}'")
        return created

    async def get_all_by_resource_class(self, resource_type: Type[T]) -> List[T]:
        """
        Retrieve all resources of a given type from the database.
        """
        crud = self._get_crud(resource_type)
        results = await crud.get_all()
        count = len(results)
        if count:
            logger.debug(f"[ResourcesHandler] Retrieved {count} record(s) of type {resource_type.__name__}")
        else:
            logger.debug(f"[ResourcesHandler] No records found for type {resource_type.__name__}")
        return results

    async def get_all(self) -> List[T]:
        resources = []
        for resource_class in self.resource_classes:
            resources.extend(await self.get_all_by_resource_class(resource_class))

        total = len(resources)
        if total:
            logger.info(f"[ResourcesHandler] Retrieved total of {total} resource(s) across all types")
        else:
            logger.warning("[ResourcesHandler] No resources found in the system")
        return resources

    async def get_by_id(self, item_id: str) -> Optional[Tuple[T, Type[T]]]:
        """
        Retrieve a resource and its type by its ID.
        """
        found = False
        resource = None
        resource_class = None
        for resource_class in self.resource_classes:
            crud = self._get_crud(resource_class)
            resource = await crud.get({"id": item_id})
            if resource:
                found = True
                break

        if not found:
            logger.error(f"[ResourcesHandler] Resource not found: no record with id={item_id}")
            raise ResourceNotFoundException(f"No Resource records found with id={item_id}")

        logger.info(
            f"[ResourcesHandler] Located {resource_class.__name__} with id={item_id}, name='{resource.name}'")
        return resource, resource_class

    async def update(self, item: T) -> bool:
        """
        Update a resource. Raises on duplicate name.
        """
        resource, resource_type = await self.get_by_id(item.id)

        crud = self._get_crud(resource_type)

        existing = await crud.get({"name": item.name})
        if existing and existing.id != item.id:
            logger.warning(f"[ResourcesHandler] Update conflict: resource with name '{item.name}' "
                           f"already exists (id={existing.id})")
            raise DuplicateResourceNameException(item.name)

        success = await crud.update({"id": item.id}, item)
        if success:
            logger.info(f"[ResourcesHandler] Successfully updated {resource_type.__name__}"
                        f" with id={item.id}, name='{item.name}'")
        else:
            logger.error(f"[ResourcesHandler] Failed to update {resource_type.__name__}"
                         f" with id={item.id}, name='{item.name}'")  # 🟩 CHANGED
        return success

    async def delete(self, item_id: str) -> bool:
        """
        Delete a resource by its ID.
        """
        resource, resource_type = await self.get_by_id(item_id)

        crud = self._get_crud(resource_type)
        success = await crud.delete({"id": item_id})
        if success:
            logger.info(
                f"[ResourcesHandler] Deleted {resource_type.__name__} with id={item_id}, name='{resource.name}'")
        else:
            logger.error(
                f"[ResourcesHandler] Delete failed: could not remove {resource_type.__name__} with id={item_id}")
        return success
