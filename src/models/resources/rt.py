from src.models.resources.abstact.base_resource import BaseResource
from src.models.resources.enums.rt_locations import RTLocations


class RT(BaseResource):
    location: RTLocations