from enum import Enum


class ResourceType(str, Enum):
    BASE = "base_resource"
    RT = "rt"
    STATION = "station"
    CRAWLER_ROUTE = "crawler_route"
    PANDEMIC_ROUTE = "pandemic_route"