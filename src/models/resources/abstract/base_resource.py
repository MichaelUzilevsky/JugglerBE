from pydantic import Field

from src.models.abstract.base_data import BaseData
from src.models.resources.enums.resource_state import ResourceState


class BaseResource(BaseData):
    name: str
    resource_state: ResourceState
    resource_type: str = Field(default_factory=lambda: "BaseResource")

    def __init__(self, **data):
        data["resource_type"] = self.__class__.__name__
        super().__init__(**data)
