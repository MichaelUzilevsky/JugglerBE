from enum import Enum


class ResourceState(str, Enum):
    PRODUCTION = "Production"
    DEVELOPMENT = "Development"
    NOT_USABLE = "Not Usable"

RESOURCE_STATE_DESCRIPTIONS = {
    ResourceState.PRODUCTION: "Resource is running in production and serves live traffic.",
    ResourceState.DEVELOPMENT: "Resource is in development mode, used for testing or staging.",
    ResourceState.NOT_USABLE: "Resource is currently unavailable for orders.",
}
