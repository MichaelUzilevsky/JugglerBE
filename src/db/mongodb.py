from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from typing import Optional
from pymongo.errors import ServerSelectionTimeoutError

from src import config, logger


class MongoDBManager:
    _instance: Optional["MongoDBManager"] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None) -> None:
        if not self._initialized:
            uri = uri or config.get_value("mongodb", "uri")
            db_name = db_name or config.get_value("mongodb", "db_name")
            self._client: AsyncIOMotorClient = AsyncIOMotorClient(uri)
            self._db_name: str = db_name
            self._db: AsyncIOMotorDatabase = self._client[db_name]
            self._initialized = True
            logger.info(f"Initializes MongoDB Manager")

    async def create_collections(self, names: list[str]) -> None:
        existing = await self._db.list_collection_names()
        for name in names:
            if name not in existing:
                await self._db.create_collection(name)
                logger.info(f"[MongoDBManager] Created collection: {name}")

    async def get_collection(self, name: str) -> AsyncIOMotorCollection:
        if not await self.is_connected():
            raise ConnectionError("[MongoDBManager] MongoDB is not reachable")

        existing_collections = await self._db.list_collection_names()
        if name not in existing_collections:
            await self._db.create_collection(name)
            logger.info(f"[MongoDBManager] Created missing MongoDB collection: {name}")

        return self._db[name]

    async def is_connected(self) -> bool:
        try:
            await self._client.admin.command("ping")
            return True
        except ServerSelectionTimeoutError:
            return False

    async def check_health(self) -> dict:
        try:
            status = await self._client.admin.command("ping")
            return {"ok": True, "status": status}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def close(self) -> None:
        self._client.close()
        logger.info(f"[MongoDBManager] Closed MongoDB Manager")
