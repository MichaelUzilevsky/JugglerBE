from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.schemas.jwt_token.jwt_token import JwtTokenCreate, JwtTokenRead, JwtTokenUpdate


class IJwtTokenRepository(ABC):
    @abstractmethod
    async def create(self, jwt_create: JwtTokenCreate) -> JwtTokenRead:
        pass

    @abstractmethod
    async def get(self, jti: str) -> Optional[JwtTokenRead]:
        pass

    @abstractmethod
    async def list(self) -> List[JwtTokenRead]:
        pass

    @abstractmethod
    async def update(self, jti: str, jwt_update: JwtTokenUpdate) -> Optional[JwtTokenRead]:
        pass

    @abstractmethod
    async def delete(self, jti: str) -> bool:
        pass

    # Convenience helper: get by raw jti (compute hash internally)
    @abstractmethod
    async def get_by_jti(self, raw_jti: str) -> Optional[JwtTokenRead]:
        pass

    @abstractmethod
    async def revoke_by_jti(self, raw_jti: str) -> bool:
        pass

    @abstractmethod
    async def mark_replaced(self, old_raw_jti: str, new_raw_jti: str) -> Optional[JwtTokenRead]:
        pass
