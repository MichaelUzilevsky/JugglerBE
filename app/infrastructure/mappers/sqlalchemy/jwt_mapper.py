from app.db.sqlalchemy.models.jwt_token import JwtRefreshToken
from app.domain.schemas.jwt_token.jwt_token import JwtTokenCreate, JwtTokenRead, JwtTokenUpdate


class JwtTokenMapper:
    @staticmethod
    def to_orm(jwt_create: JwtTokenCreate) -> JwtRefreshToken:
        """
        Map JwtTokenCreate schema → ORM Jwt Token object
        """
        return JwtRefreshToken(
            id=jwt_create.id,
            user_id=jwt_create.user_id,
            expires_at=jwt_create.expires_at,
        )

    @staticmethod
    def to_read(jwt_token: JwtRefreshToken) -> JwtTokenRead:
        """
        Map ORM JwtRefreshToken → JwtTokenRead schema
        """
        return JwtTokenRead.model_validate(jwt_token)

    @staticmethod
    def update_orm(orm_obj: JwtRefreshToken, update_schema: JwtTokenUpdate) -> None:
        # Apply only set fields
        if update_schema.revoked is not None:
            orm_obj.revoked = update_schema.revoked
        if update_schema.replaced_by is not None:
            orm_obj.replaced_by = update_schema.replaced_by
        if update_schema.expires_at is not None:
            orm_obj.expires_at = update_schema.expires_at
