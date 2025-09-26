from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any


class AbstractDBManager(ABC):
    """
    Generic asynchronous Database Manager Interface.

    This is designed to be implemented by SQL, NoSQL, or other DB managers.
    """

    @abstractmethod
    async def get_connection(self) -> AsyncGenerator[Any, None]:
        """
        Yield a database session, connection, or client reference.

        SQL example: AsyncSession
        Mongo example: Motor Database instance
        """
        pass

    @abstractmethod
    async def transaction(self, conn: Any) -> AsyncGenerator[Any, None]:
        """
        Context manager for transactional operations.
        For SQL: yields session with commit/rollback
        For NoSQL: may just yield connection
        """
        pass

    @abstractmethod
    async def check_connection(self) -> bool:
        """
        Check if the database connection is alive.

        Should return True if the DB is reachable, False otherwise.
        """
        pass

    @abstractmethod
    async def close(self):
        """
        Close or dispose of database resources.
        """
        pass

    @property
    @abstractmethod
    def raw(self) -> Any:
        """
        Access the raw underlying client/engine object directly.

        Example:
            SQLAlchemy: AsyncEngine
            Mongo: AsyncIOMotorClient
        """
        pass
