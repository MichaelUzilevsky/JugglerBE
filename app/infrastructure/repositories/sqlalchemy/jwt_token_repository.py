from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sqlalchemy.models.jwt_token import JwtRefreshToken
from app.domain.repositories.ijwt_token_repository import IJwtTokenRepository
from app.domain.schemas.jwt_token.jwt_token import JwtTokenRead, JwtTokenCreate, JwtTokenUpdate
from app.infrastructure.mappers.sqlalchemy.jwt_mapper import JwtTokenMapper
from app.infrastructure.repositories.sqlalchemy.base_repository import SQLAlchemyBaseRepository
from app.utils.jti import hash_jti


class SQLAlchemyJwtTokenRepository(
    SQLAlchemyBaseRepository[JwtTokenRead, JwtTokenCreate, JwtTokenUpdate, JwtRefreshToken],
    IJwtTokenRepository,
):

    def __init__(self, session: AsyncSession):
        super().__init__(session, JwtRefreshToken, JwtTokenMapper)

    # Convenience helper: get by raw jti (compute hash internally)
    async def get_by_jti(self, raw_jti: str) -> Optional[JwtTokenRead]:
        key = hash_jti(raw_jti)
        token = await self.get(key)
        self._log_debug(
            event="get_success",
            msg=f"Fetched jwt_token with id={key}",
            extra={"id": key}
        )
        return token

    async def revoke_by_jti(self, raw_jti: str) -> bool:
        key = hash_jti(raw_jti)
        update_schema = JwtTokenUpdate(revoked=True)
        revoked = await self.update(key, update_schema)
        self._log_debug(
            event="revoke_success",
            msg=f"Revoked jwt_token with id={key}",
            extra={"id": key}
        )
        return revoked is not None

    async def mark_replaced(self, old_raw_jti: str, new_raw_jti: str) -> Optional[JwtTokenRead]:
        old_key = hash_jti(old_raw_jti)
        new_key = hash_jti(new_raw_jti)
        update_schema = JwtTokenUpdate(revoked=True, replaced_by=new_key)
        replaced = await self.update(old_key, update_schema)
        self._log_debug(
            event="token_replace_success",
            msg=f"Replaced jwt_token with id={old_key} to new token with id={new_key}",
            extra={"old_token_id": old_key, "new_token_id": new_key}
        )
        return replaced
