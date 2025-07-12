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
                logger.debug(f"[ResourcesHandler] Mapped {cls.__name__} to collection '{collection_name}'")
            except KeyError:
                logger.warning(f"[ResourcesHandler] No collection mapping found for resource class '{cls.__name__}'")

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
            logger.warning(f"[ResourcesHandler] Duplicate resource name '{item.name}' on create")
            raise DuplicateResourceNameException(item.name)

        created = await crud.create(item)
        if created:
            logger.info(f"[ResourcesHandler] Successfully created {resource_type.__name__} with id={created.id}")
        else:
            logger.warning(f"[ResourcesHandler] Failed to create {resource_type.__name__}")
        return created

    async def get_all_by_resource_class(self, resource_type: Type[T]) -> List[T]:
        """
        Retrieve all resources of a given type from the database.
        """
        crud = self._get_crud(resource_type)
        results = await crud.get_all()
        count = len(results)
        if count:
            logger.info(f"[ResourcesHandler] Retrieved {count} {resource_type.__name__}(s) from the database")
        else:
            logger.warning(f"[ResourcesHandler] No {resource_type.__name__} records found")
        return results

    async def get_all(self) -> List[T]:
        resources = []
        for resource_class in self.resource_classes:
            resources.extend(await self.get_all_by_resource_class(resource_class))
        if len(resources):
            logger.info(f"[ResourcesHandler] Retrieved {len(resources)} Resources from the database")
        else:
            logger.warning(f"[ResourcesHandler] No Resource records found")
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
            logger.error(f"[ResourcesHandler] No Resource records found with id={item_id}")
            raise ResourceNotFoundException(f"No Resource records found with id={item_id}")
        
        if resource:
            logger.info(f"[ResourcesHandler] Found {resource_class.__name__} with id={item_id}")
            
        return resource, resource_class

    async def update(self, item: T) -> bool:
        """
        Update a resource. Raises on duplicate name.
        """
        resource, resource_type = await self.get_by_id(item.id)

        crud = self._get_crud(resource_type)

        existing = await crud.get({"name": item.name})
        if existing and existing.id != item.id:
            logger.warning(f"[ResourcesHandler] Duplicate resource name '{item.name}' on update")
            raise DuplicateResourceNameException(item.name)

        success = await crud.update({"id": item.id}, item)
        if success:
            logger.info(f"[ResourcesHandler] Updated {resource_type.__name__} with id={item.id}")
        else:
            logger.warning(f"[ResourcesHandler] Failed to update {resource_type.__name__} with id={item.id}")
        return success

    async def delete(self, item_id: str) -> bool:
        """
        Delete a resource by its ID.
        """
        resource, resource_type = await self.get_by_id(item_id)

        crud = self._get_crud(resource_type)
        success = await crud.delete({"id": item_id})
        if success:
            logger.info(f"[ResourcesHandler] Deleted {resource_type.__name__} with id={item_id}")
        else:
            logger.warning(f"[ResourcesHandler] Failed to delete {resource_type.__name__} with id={item_id}")
        return success
