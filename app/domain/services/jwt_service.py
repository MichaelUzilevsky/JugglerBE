from datetime import datetime, timezone, timedelta
from typing import Tuple

from app import config, logger
from app.domain.repositories.ijwt_token_repository import IJwtTokenRepository
from app.domain.schemas.jwt_token.jwt_token import JwtTokenCreate
from app.exceptions.jwt_exceptions.jwt_exceptions import InvalidJwtPayloadException, JwtNotFoundException, \
    JwtRevokedException, JwtExpiredException
from app.utils.jti import new_jti, hash_jti
from app.utils.jwt import create_refresh_token_jwt, create_access_token, decode_refresh_token_jwt


class JWTService:
    def __init__(self, jwt_repo: IJwtTokenRepository):
        self.jwt_repo = jwt_repo

    async def create_and_store_refresh_token(self, user_id: int, username: str) -> Tuple[str, str, str]:
        """
        Create a new refresh token (raw jti), store hashed jti as PK, and return (access_jwt, refresh_jwt, raw_jti).
        """
        raw_jti = new_jti()
        jti_hash = hash_jti(raw_jti)
        refresh_token_expire_days = int(config.get_value("jwt_tokens", "refresh_token_expire_days"))
        expires_at = datetime.now(timezone.utc) + timedelta(days=refresh_token_expire_days)

        create_schema = JwtTokenCreate(id=jti_hash, user_id=user_id, expires_at=expires_at)
        await self.jwt_repo.create(create_schema)

        refresh_jwt = create_refresh_token_jwt(username=username, raw_jti=raw_jti)
        access_jwt = create_access_token(username=username)

        logger.info(
            f"Issued new refresh token for user '{username}' (id={user_id})",
            extra={
                "event": "jwt_create_success",
                "user_id": user_id,
                "username": username,
                "jti_hash": jti_hash,
                "expires_at": expires_at.isoformat(),
            }
        )

        return access_jwt, refresh_jwt, raw_jti

    async def rotate_refresh_token(self, refresh_jwt: str) -> Tuple[str, str]:
        """
        Validate the provided refresh_jwt, check DB, rotate it (create new token and revoke old),
        and return (new_access_jwt, new_refresh_jwt).
        """
        payload = decode_refresh_token_jwt(refresh_jwt)
        username = payload.get("sub")
        raw_jti = payload.get("jti")
        if not (username and raw_jti):
            logger.warning(
                "Refresh token rotation failed: missing username or jti in payload",
                extra={"event": "jwt_rotate_invalid_payload"},
            )
            raise InvalidJwtPayloadException("Invalid refresh token payload")

        jti_hash = hash_jti(raw_jti)

        # Lookup the record in DB
        db_token = await self.jwt_repo.get_by_jti(raw_jti)
        if not db_token:
            logger.warning(
                "Refresh token rotation failed: token not found in DB",
                extra={"event": "jwt_rotate_not_found", "jti_hash": jti_hash},
            )
            raise JwtNotFoundException("refresh token not found")

        if db_token.revoked:
            logger.warning(
                f"Refresh token rotation failed: token already revoked for user_id={db_token.user_id}",
                extra={"event": "jwt_rotate_revoked", "jti_hash": jti_hash, "user_id": db_token.user_id},
            )
            raise JwtRevokedException("refresh token revoked")

        if db_token.expires_at <= datetime.now(timezone.utc):
            logger.warning(
                f"Refresh token rotation failed: token expired for user_id={db_token.user_id}",
                extra={
                    "event": "jwt_rotate_expired",
                    "jti_hash": jti_hash,
                    "user_id": db_token.user_id,
                    "expires_at": db_token.expires_at.isoformat(),
                },
            )
            raise JwtExpiredException("refresh token expired")

        # Create new token & DB entry
        new_raw_jti = new_jti()
        new_jti_hash = hash_jti(new_raw_jti)
        refresh_token_expire_days = int(config.get_value("jwt_tokens", "refresh_token_expire_days"))
        new_expires = datetime.now(timezone.utc) + timedelta(days=refresh_token_expire_days)

        create_schema = JwtTokenCreate(id=new_jti_hash, user_id=db_token.user_id, expires_at=new_expires)

        await self.jwt_repo.create(create_schema)

        # Mark old one replaced + revoked
        await self.jwt_repo.mark_replaced(old_raw_jti=raw_jti, new_raw_jti=new_raw_jti)

        # Build tokens to return
        new_refresh_jwt = create_refresh_token_jwt(username=username, raw_jti=new_raw_jti)
        new_access_jwt = create_access_token(username=username)

        logger.info(
            f"Rotated refresh token for user '{username}' (id={db_token.user_id})",
            extra={
                "event": "jwt_rotate_success",
                "old_jti_hash": jti_hash,
                "new_jti_hash": new_jti_hash,
                "user_id": db_token.user_id,
                "username": username,
                "expires_at": new_expires.isoformat(),
            }
        )

        return new_access_jwt, new_refresh_jwt

    async def revoke_refresh_token(self, refresh_jwt: str) -> bool:
        """
        Revoke token by raw jti (used on logout).
        """
        payload = decode_refresh_token_jwt(refresh_jwt)
        raw_jti = payload.get("jti")
        if not raw_jti:
            logger.warning(
                "Refresh token revocation failed: missing jti in payload",
                extra={"event": "jwt_revoke_invalid_payload"},
            )
            raise InvalidJwtPayloadException("Invalid refresh token payload")

        jti_hash = hash_jti(raw_jti)
        result = await self.jwt_repo.revoke_by_jti(raw_jti)

        logger.info(
            "Refresh token revoked (logout)",
            extra={
                "event": "jwt_revoke_success",
                "jti_hash": jti_hash,
                "result": result,
            }
        )

        return result
