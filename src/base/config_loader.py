import os
import yaml
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

class ConfigLoader:
    _instance = None

    def __new__(cls):
        """
        Singleton pattern for ConfigLoader. Loads configuration on first instantiation.
        """
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._config = {}
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """
        Loads configuration from YAML files and .env file based on the environment.
        """
        # Load .env file if exists
        dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if dotenv_path.exists():
            load_dotenv(dotenv_path)

        env = os.environ.get("APP_ENV", "base").lower()
        base_path = Path(__file__).resolve().parent.parent.parent / "configs" / "app"
        base_config_path = base_path / "base.yaml"
        env_config_path = base_path / f"{env}.yaml"

        with open(base_config_path, "r") as f:
            base_config = yaml.safe_load(f) or {}

        if env != "base" and env_config_path.exists():
            with open(env_config_path, "r") as f:
                env_config = yaml.safe_load(f) or {}
            self._config = self._deep_merge_dicts(base_config, env_config)
        else:
            self._config = base_config

    def _deep_merge_dicts(self, base: dict, override: dict) -> dict:
        """
        Recursively merges two dictionaries.
        """
        result = base.copy()
        for key, value in override.items():
            if (
                key in result and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge_dicts(result[key], value)
            else:
                result[key] = value
        return result

    def get_value(self, *keys: str) -> Any:
        """
        Retrieves a value from the loaded config using a sequence of keys.
        Returns None if the key path does not exist.
        """
        ref = self._config
        for key in keys:
            if isinstance(ref, dict) and key in ref:
                ref = ref[key]
            else:
                return None
        return ref


config = ConfigLoader()
