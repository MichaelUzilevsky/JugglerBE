from typing import Type, TypeVar, Generic, Optional, Any, List, Dict

from bson import ObjectId
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

    @staticmethod
    def _adapt_data_from_mongo(doc: Dict) -> Dict:
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    @staticmethod
    def _adapt_data_to_mongo(model: T) -> dict:
        doc = model.model_dump(exclude_none=True)
        if "id" in doc:
            doc["_id"] = ObjectId(doc.pop("id"))
        return doc

    @staticmethod
    def _normalize_filter(filter_dict: dict) -> dict:
        if "id" in filter_dict:
            filter_dict["_id"] = ObjectId(filter_dict.pop("id"))
        return filter_dict

    async def create(self, item: T) -> T:
        collection = await self._get_collection()
        doc = self._adapt_data_to_mongo(item)
        result = await collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        return self.model(**doc)

    async def get(self, data_filter: Optional[Any] = None) -> Optional[T]:
        collection = await self._get_collection()
        filters = self._normalize_filter(data_filter)
        document = await collection.find_one(filters)
        return self.model(**self._adapt_data_from_mongo(dict(document))) if document else None

    async def get_all(self, data_filter: Optional[Any] = None) -> List[T]:
        collection = await self._get_collection()
        cursor = collection.find(data_filter)
        return [self.model(**self._adapt_data_from_mongo(dict(doc))) async for doc in cursor]

    async def update(self, data_filter: Optional[Any], update_data: T) -> bool:
        collection = await self._get_collection()
        update_dict = {"$set": self._adapt_data_to_mongo(update_data)}
        filters = self._normalize_filter(data_filter)
        result = await collection.update_one(filters, update_dict)
        return result.modified_count > 0

    async def delete(self, data_filter: Optional[Any]) -> bool:
        collection = await self._get_collection()
        filters = self._normalize_filter(data_filter)
        result = await collection.delete_one(filters)
        return result.deleted_count > 0