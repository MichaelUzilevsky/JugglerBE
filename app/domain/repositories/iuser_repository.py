from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.schemas.user.user import UserCreate, UserRead, UserUpdate


class IUserRepository(ABC):
    @abstractmethod
    async def create(self, user_create: UserCreate) -> UserRead:
        pass

    @abstractmethod
    async def get(self, user_id: int) -> Optional[UserRead]:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[UserRead]:
        pass

    @abstractmethod
    async def list(self) -> List[UserRead]:
        pass

    @abstractmethod
    async def update(self, user_id: int, user_update: UserUpdate) -> Optional[UserRead]:
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        pass
