from src.models.abstract.base_data import BaseData


class UserLogin(BaseData):
    username: str
    password: str
