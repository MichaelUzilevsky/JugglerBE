from src.models.resources.abstract.base_resource import BaseResource
from src.models.resources.enums.rt_locations import RtLocations


class Rt(BaseResource):
    location: RtLocations
