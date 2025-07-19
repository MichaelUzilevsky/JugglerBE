from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Any, List

T = TypeVar("T")


class ICrud(ABC, Generic[T]):
    @abstractmethod
    async def create(self, item: T) -> T:
        """
        Create a new item in the data store.
        """

    @abstractmethod
    async def get(self, data_filter: Optional[Any] = None) -> Optional[T]:
        """
        Retrieve a single item matching the filter from the data store.
        """

    @abstractmethod
    async def get_all(self, data_filter: Optional[Any] = None) -> List[T]:
        """
        Retrieve all items matching the filter from the data store.
        """

    @abstractmethod
    async def update(self, data_filter: Optional[Any], update_data: T) -> bool:
        """
        Update an item matching the filter with new data.
        """

    @abstractmethod
    async def delete(self, data_filter: Optional[Any]) -> bool:
        """
        Delete an item matching the filter from the data store.
        """
