from pydantic import BaseModel

from src.models.users.enums.user_role import UserRole
from src.models.users.user import User


class UserSignupRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: str

    def to_model(self) -> User:
        return User(
            username=self.username,
            password=self.password,
            full_name=self.full_name,
            email=self.email,
            role=UserRole.USER
        )
