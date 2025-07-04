from typing import Type, TypeVar, Generic, Optional, Callable, Any, List
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorCollection

from .icrud import ICrud
from .mongodb import MongoDBManager

T = TypeVar("T", bound=BaseModel)

class MongoCrud(Generic[T], ICrud[T]):
    def __init__(self, model: Type[T], collection_name: str) -> None:
        self.model = model
        self.collection_name = collection_name
        self.db = MongoDBManager()

    async def _get_collection(self) -> AsyncIOMotorCollection:
        return await self.db.get_collection(self.collection_name)

    async def create(self, item: T) -> T:
        collection = await self._get_collection()
        item_dict = item.model_dump(by_alias=True, exclude_none=True)
        result = await collection.insert_one(item_dict)
        item_dict["_id"] = result.inserted_id
        return self.model(**item_dict)

    async def get(self, filter_func: Optional[Callable[[Any], Any]] = None) -> Optional[T]:
        collection = await self._get_collection()
        filters = filter_func(None) if filter_func else {}
        document = await collection.find_one(filters)
        return self.model(**document) if document else None

    async def get_all(self, filter_func: Optional[Callable[[Any], Any]] = None) -> List[T]:
        collection = await self._get_collection()
        filters = filter_func(None) if filter_func else {}
        cursor = collection.find(filters)
        return [self.model(**doc) async for doc in cursor]

    async def update(self, filter_func: Callable[[Any], Any], update_data: T) -> bool:
        collection = await self._get_collection()
        filters = filter_func(None)
        update_dict = {"$set": update_data.model_dump(by_alias=True, exclude_none=True)}
        result = await collection.update_one(filters, update_dict)
        return result.modified_count > 0

    async def delete(self, filter_func: Callable[[Any], Any]) -> bool:
        collection = await self._get_collection()
        filters = filter_func(None)
        result = await collection.delete_one(filters)
        return result.deleted_count > 0