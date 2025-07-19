from src.models.resources.abstract.base_resource import BaseResource
from src.models.resources.enums.resources_environmets import ResourceEnvironments


class BaseVirtualResource(BaseResource):
    environment: ResourceEnvironments
