from typing import Dict

from src import config
from src.handlers.resources_handler import ResourcesHandler


def get_resources_handler() -> ResourcesHandler:
    resources_config: Dict = config.get_value("mongodb", "collections", "resources")
    resource_handler: ResourcesHandler = ResourcesHandler(resources_config)
    return resource_handler
