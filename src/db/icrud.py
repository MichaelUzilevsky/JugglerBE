from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Callable, Any, List

T = TypeVar("T")

class ICrud(ABC, Generic[T]):
    @abstractmethod
    async def create(self, item: T) -> T: ...

    @abstractmethod
    async def get(self, filter_func: Optional[Callable[[Any], Any]] = None) -> Optional[T]: ...

    @abstractmethod
    async def get_all(self, filter_func: Optional[Callable[[Any], Any]] = None) -> List[T]: ...

    @abstractmethod
    async def update(self, filter_func: Callable[[Any], Any], update_data: T) -> bool: ...

    @abstractmethod
    async def delete(self, filter_func: Callable[[Any], Any]) -> bool: ...