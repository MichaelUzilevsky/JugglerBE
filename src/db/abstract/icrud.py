from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Any, List

T = TypeVar("T")

class ICrud(ABC, Generic[T]):
    @abstractmethod
    async def create(self, item: T) -> T: ...

    @abstractmethod
    async def get(self, data_filter: Optional[Any] = None) -> Optional[T]: ...

    @abstractmethod
    async def get_all(self, data_filter: Optional[Any] = None) -> List[T]: ...

    @abstractmethod
    async def update(self, data_filter: Optional[Any], update_data: T) -> bool: ...

    @abstractmethod
    async def delete(self, data_filter: Optional[Any]) -> bool: ...
