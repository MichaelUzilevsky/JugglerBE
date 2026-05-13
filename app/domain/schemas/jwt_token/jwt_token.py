from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ----------------- Create -----------------
class JwtTokenCreate(BaseModel):
    id: str  # hashed jti (sha256 hex) -> used as primary key
    user_id: int
    expires_at: datetime


# ----------------- Read -----------------
class JwtTokenRead(BaseModel):
    id: str
    user_id: int
    created_at: datetime
    expires_at: datetime
    revoked: bool
    replaced_by: Optional[str]

    model_config = {"from_attributes": True}


# ----------------- Update -----------------
class JwtTokenUpdate(BaseModel):
    """Fields allowed to update via base repo update method."""
    revoked: Optional[bool] = None
    replaced_by: Optional[str] = None
    expires_at: Optional[datetime] = None
