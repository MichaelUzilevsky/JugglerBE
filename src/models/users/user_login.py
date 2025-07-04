from src.models.base_data import BaseData


class UserLogin(BaseData):
    username: str
    password: str