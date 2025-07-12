from pydoc import locate
from typing import List, Type, Dict

from src import config, logger
from src.models.resources.abstact.base_resource import BaseResource

class ProjectResources:
    @staticmethod
    def _get_resource_class_by_fullname(class_path: str):
        """
        Locate and return a class object by its full import path string.
        """
        return locate(class_path)

    @staticmethod
    def _change_to_class_format(name: str) -> str:
        """
        Converts a snake_case name (e.g., 'crawler_routes') to PascalCase (e.g., 'CrawlerRoute').
        Removes the trailing 's'.
        """
        return name[:-1].replace("_", " ").title().replace(" ", "")

    @staticmethod
    def retrieve_project_resources(resources_config_data: Dict) -> List[Type[BaseResource]]:
        """
        Retrieve all resource classes defined in the config file.
        Returns a list of BaseResource subclasses.
        Raises ValueError if the config is missing the resources section.
        """

        resource_classes = []

        for key in resources_config_data.keys():
            class_name = ProjectResources._change_to_class_format(key)
            class_path = f"src.models.resources.{key[:-1]}.{class_name}"

            try:
                cls = ProjectResources._get_resource_class_by_fullname(class_path)

                if cls is None:
                    logger.warning(f"[Utils] Could not locate class '{class_name}' "
                                   f"at '{class_path}' — skipping")
                    continue

                if not isinstance(cls, type):
                    logger.warning(f"[Utils] Located object '{class_name}' is not a class — skipping")
                    continue

                if not issubclass(cls, BaseResource):
                    logger.warning(f"[Utils] Class '{class_name}' is not a subclass of BaseResource — skipping")
                    continue

                resource_classes.append(cls)
                logger.debug(f"[Utils] Successfully loaded resource class: {class_name} from config key '{key}'")

            except Exception as e:
                logger.error(f"[Utils] Failed to load class for config key '{key}': {e}")

        return resource_classes
