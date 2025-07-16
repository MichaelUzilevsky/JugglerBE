from pydantic import BaseModel

from src.models.users.enums.user_role import UserRole
from src.models.users.user import User


class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    email: str
    role: UserRole

    @classmethod
    def from_model(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
        )
