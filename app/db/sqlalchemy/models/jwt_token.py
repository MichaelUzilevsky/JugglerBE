from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index, ForeignKey

from app.db.sqlalchemy.base import Base


class JwtRefreshToken(Base):
    __tablename__ = "jwt_refresh_tokens"

    # id is the SHA-256 hex of the raw jti and serves as the PK (string length 64)
    id = Column(String(64), primary_key=True, index=True)  # hashed jti (sha256 hex)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked = Column(Boolean(), default=False, nullable=False)
    replaced_by = Column(String(64), nullable=True)  # jti_hash of the new token when rotated

    __table_args__ = (
        Index("ix_jti_hash_user", "id", "user_id"),
    )
