from typing import Type, TypeVar, List, Dict, Optional

from src import config, logger
from src.db.mongo_crud import MongoCrud
from src.db.icrud import ICrud
from src.exceptions.resources_exceptions.duplicate_resource_name_exception import DuplicateResourceNameException
from src.models.resources.abstact.base_resource import BaseResource

T = TypeVar("T", bound=BaseResource)

class ResourcesHandler:
    def __init__(self, resource_classes: List[Type[T]]) -> None:
        self._class_to_crud: Dict[Type[T], ICrud[T]] = {}
        self._initialize_cruds(resource_classes)

    def _initialize_cruds(self, resource_classes: List[Type[T]]) -> None:
        for cls in resource_classes:
            collection_key = self._get_collection_key(cls.__name__)
            try:
                collection_name = config.get_value("mongodb", "collections", "resources", collection_key)
                self._class_to_crud[cls] = MongoCrud(cls, collection_name)
                logger.info(f"[ResourcesManager] Mapped {cls.__name__} to collection '{collection_name}'")
            except KeyError:
                logger.warning(f"[ResourcesManager] No collection mapping found for resource class '{cls.__name__}'")

    def _get_crud(self, resource_type: Type[T]) -> ICrud[T]:
        if resource_type not in self._class_to_crud:
            error_msg = f"[ResourcesManager] No CRUD instance mapped for resource type: {resource_type.__name__}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        return self._class_to_crud[resource_type]

    @staticmethod
    def _get_collection_key(class_name: str) -> str:
        import re
        snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
        return f"{snake_case}s"

    async def create(self, resource_type: Type[T], item: T) -> T:
        crud = self._get_crud(resource_type)

        existing = await crud.get({"name": item.name})
        if existing:
            logger.warning(f"[ResourcesManager] Duplicate resource name '{item.name}' on create")
            raise DuplicateResourceNameException(item.name)

        created = await crud.create(item)
        if created:
            logger.info(f"[ResourcesManager] Successfully created {resource_type.__name__} with id={created.id}")
        else:
            logger.warning(f"[ResourcesManager] Failed to create {resource_type.__name__}")
        return created

    async def get_all(self, resource_type: Type[T]) -> List[T]:
        crud = self._get_crud(resource_type)
        results = await crud.get_all()
        count = len(results)
        if count:
            logger.info(f"[ResourcesManager] Retrieved {count} {resource_type.__name__}(s) from the database")
        else:
            logger.warning(f"[ResourcesManager] No {resource_type.__name__} records found")
        return results

    async def get_by_id(self, resource_type: Type[T], item_id: str) -> Optional[T]:
        crud = self._get_crud(resource_type)
        result = await crud.get({"id": item_id})
        if result:
            logger.info(f"[ResourcesManager] Found {resource_type.__name__} with id={item_id}")
        else:
            logger.warning(f"[ResourcesManager] {resource_type.__name__} with id={item_id} not found")
        return result

    async def update(self, resource_type: Type[T], item: T) -> bool:
        crud = self._get_crud(resource_type)

        existing = await crud.get({"name": item.name})
        if existing and existing.id != item.id:
            logger.warning(f"[ResourcesManager] Duplicate resource name '{item.name}' on update")
            raise DuplicateResourceNameException(item.name)

        success = await crud.update({"id": item.id}, item)
        if success:
            logger.info(f"[ResourcesManager] Updated {resource_type.__name__} with id={item.id}")
        else:
            logger.warning(f"[ResourcesManager] Failed to update {resource_type.__name__} with id={item.id}")
        return success

    async def delete(self, resource_type: Type[T], item_id: str) -> bool:
        crud = self._get_crud(resource_type)
        success = await crud.delete({"id": item_id})
        if success:
            logger.info(f"[ResourcesManager] Deleted {resource_type.__name__} with id={item_id}")
        else:
            logger.warning(f"[ResourcesManager] Failed to delete {resource_type.__name__} with id={item_id}")
        return success
