from pydoc import locate
from typing import List, Type

from src import config, logger
from src.models.resources.abstact.base_resource import BaseResource


def get_resource_class_by_fullname(class_path: str):
    """
    Locate and return a class object by its full import path string.
    """
    return locate(class_path)


def change_to_class_format(name: str) -> str:
    """
    Converts a snake_case name (e.g., 'crawler_routes') to PascalCase (e.g., 'CrawlerRoute').
    Removes the trailing 's'.
    """
    return name[:-1].replace("_", " ").title().replace(" ", "")


def get_all_resource_classes_from_config() -> List[Type[BaseResource]]:
    """
    Retrieve all resource classes defined in the config file.
    Returns a list of BaseResource subclasses.
    Raises ValueError if the config is missing the resources section.
    """
    try:
        config_resources = config.get_value("mongodb", "collections", "resources")
    except KeyError as e:
        logger.error("[ResourcesManager] Missing 'resources' section in config.yaml: %s", str(e))
        raise ValueError("[ResourcesManager] No 'resources' section in config")

    resource_classes = []

    for key in config_resources.keys():
        class_name = change_to_class_format(key)
        class_path = f"src.models.resources.{key[:-1]}.{class_name}"

        try:
            cls = get_resource_class_by_fullname(class_path)

            if cls is None:
                logger.warning(f"[ResourcesManager] Could not locate class '{class_name}' "
                               f"at '{class_path}' — skipping")
                continue

            if not isinstance(cls, type):
                logger.warning(f"[ResourcesManager] Located object '{class_name}' is not a class — skipping")
                continue

            if not issubclass(cls, BaseResource):
                logger.warning(f"[ResourcesManager] Class '{class_name}' is not a subclass of BaseResource — skipping")
                continue

            resource_classes.append(cls)
            logger.info(f"[ResourcesManager] Successfully loaded resource class: {class_name} from config key '{key}'")

        except Exception as e:
            logger.error(f"[ResourcesManager] Failed to load class for config key '{key}': {e}")

    return resource_classes
