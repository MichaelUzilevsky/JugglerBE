from enum import Enum


class ResourceState(str, Enum):
    PRODUCTION = "Production"
    DEVELOPMENT = "Development"
    NOT_USABLE = "Not Usable"
