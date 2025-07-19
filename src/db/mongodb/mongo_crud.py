from typing import Type, TypeVar, Generic, Optional, Any, List, Dict

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel

from src.db.abstract.icrud import ICrud
from src.db.mongodb.mongodb import MongoDBManager

T = TypeVar("T", bound=BaseModel)


class MongoCrud(Generic[T], ICrud[T]):
    def __init__(self, model: Type[T], collection_name: str) -> None:
        """
        Initialize MongoCrud with a model type and collection name.
        """
        self.model = model
        self.collection_name = collection_name
        self.db = MongoDBManager()

    async def _get_collection(self) -> AsyncIOMotorCollection:
        """
        Retrieve the MongoDB collection for this CRUD instance.
        """
        return await self.db.get_collection(self.collection_name)

    @staticmethod
    def _adapt_data_from_mongo(doc: Dict) -> Dict:
        """
        Convert MongoDB document to model dictionary, renaming _id to id.
        """
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    @staticmethod
    def _adapt_data_to_mongo(model: T) -> dict:
        """
        Convert a model instance to a MongoDB document dictionary.
        """
        doc = model.model_dump(exclude_none=True)
        if "id" in doc:
            doc["_id"] = ObjectId(doc.pop("id"))
        return doc

    @staticmethod
    def _normalize_filter(filter_dict: dict) -> dict:
        """
        Recursively normalize filter dictionary, converting 'id' to '_id' and strings to ObjectId.
        """

        def normalize(d: dict) -> dict:
            if not d:
                return d
            new_dict = {}
            for key, value in d.items():
                if isinstance(value, dict):
                    value = normalize(value)
                # If the key is 'id', convert to '_id' and handle special operators
                if key == "id":
                    new_dict["_id"] = MongoCrud._convert_to_object_id(value)
                else:
                    new_dict[key] = value
            return new_dict

        return normalize(filter_dict)

    @staticmethod
    def _convert_to_object_id(value: Any) -> Any:
        """
        Convert string or operator dict to ObjectId or a dict of ObjectId(s).
        """
        if isinstance(value, str):
            return ObjectId(value)
        elif isinstance(value, dict):
            return {k: ObjectId(v) if isinstance(v, str) else v for k, v in value.items()}
        else:
            return value

    async def create(self, item: T) -> T:
        """
        Insert a new item into the collection and return the created model instance.
        """
        collection = await self._get_collection()
        doc = self._adapt_data_to_mongo(item)
        result = await collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        return self.model(**doc)

    async def get(self, data_filter: Optional[Any] = None) -> Optional[T]:
        """
        Retrieve a single item matching the filter from the collection.
        """
        collection = await self._get_collection()
        filters = self._normalize_filter(data_filter)
        document = await collection.find_one(filters)
        return self.model(**self._adapt_data_from_mongo(dict(document))) if document else None

    async def get_all(self, data_filter: Optional[Any] = None) -> List[T]:
        """
        Retrieve all items matching the filter from the collection.
        """
        collection = await self._get_collection()
        filters = self._normalize_filter(data_filter)
        cursor = collection.find(filters)
        return [self.model(**self._adapt_data_from_mongo(dict(doc))) async for doc in cursor]

    async def update(self, data_filter: Optional[Any], update_data: T) -> bool:
        """
        Update an item matching the filter with new data. Returns True if updated.
        """
        collection = await self._get_collection()
        update_dict = {"$set": self._adapt_data_to_mongo(update_data)}
        filters = self._normalize_filter(data_filter)
        result = await collection.update_one(filters, update_dict)
        return result.modified_count > 0

    async def delete(self, data_filter: Optional[Any]) -> bool:
        """
        Delete an item matching the filter from the collection. Returns True if deleted.
        """
        collection = await self._get_collection()
        filters = self._normalize_filter(data_filter)
        result = await collection.delete_one(filters)
        return result.deleted_count > 0
