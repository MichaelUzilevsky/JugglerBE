from src.models.abstract.base_data import BaseData
from src.models.resources.enums.resource_state import ResourceState


class BaseResource(BaseData):
    name: str
    is_orderable: bool = False
    resource_state: ResourceState
