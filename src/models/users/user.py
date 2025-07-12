from src.models.abstract.base_data import BaseData
from src.models.users.enums.user_role import UserRole


class User(BaseData):
    username: str
    password: str
    full_name: str
    email: str
    role: UserRole = UserRole.USER
