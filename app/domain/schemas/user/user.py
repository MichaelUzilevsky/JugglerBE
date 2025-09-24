from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.domain.schemas.user.enums.user_role import UserRole


# ----------------- Create -----------------
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: str
    role: UserRole = UserRole.USER


# ----------------- Update -----------------
class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None


# ----------------- Read -----------------
class UserRead(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserReadInternal(UserRead):
    password: str
