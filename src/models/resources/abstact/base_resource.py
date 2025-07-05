from src.models.abstract.base_data import BaseData


class BaseResource(BaseData):
    name: str
    is_orderable: bool = False
