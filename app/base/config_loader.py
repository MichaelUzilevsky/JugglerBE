import os
import re
from pathlib import Path
from typing import Any

import yaml


class ConfigLoader:
    _instance = None
    ENV_VAR_PATTERN = re.compile(r"\${([^}^{]+)}")

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

        env = os.environ.get("APP_ENV", "base").lower()
        base_path = Path(__file__).resolve().parent.parent / "configs" / "app"
        base_config_path = base_path / "base.yaml"
        env_config_path = base_path / f"{env}.yaml"

        with open(base_config_path, "r") as f:
            base_config = yaml.safe_load(f) or {}

        if env != "base" and env_config_path.exists():
            with open(env_config_path, "r") as f:
                env_config = yaml.safe_load(f) or {}
            merged = self._deep_merge_dicts(base_config, env_config)
        else:
            merged = base_config

        # Step 1: Resolve ${VAR} placeholders
        resolved = self._resolve_env_vars(merged)

        # Step 2: Apply full env var overrides
        overridden = self._apply_env_overrides(resolved)

        self._config = overridden

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

    def _resolve_env_vars(self, value):
        """
        Recursively resolves ${VAR_NAME} using environment variables.
        """
        if isinstance(value, dict):
            return {k: self._resolve_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_env_vars(i) for i in value]
        elif isinstance(value, str):
            match = ConfigLoader.ENV_VAR_PATTERN.search(value)
            if match:
                env_var = match.group(1)
                env_value = os.environ.get(env_var)
                if env_value is None:
                    raise ValueError(f"Environment variable '{env_var}' not set.")
                return ConfigLoader.ENV_VAR_PATTERN.sub(env_value, value)
        return value

    def _apply_env_overrides(self, config: dict, prefix: str = "") -> dict:
        """
        Recursively checks for environment variables that override config values.
        Nested keys become ENV vars with underscores.
        Example: postgresql.User -> POSTGRESQL_USER
        """
        new_config = {}
        for key, value in config.items():
            env_key = f"{prefix}{key}".upper()
            env_key = env_key.replace(".", "_")

            if isinstance(value, dict):
                new_config[key] = self._apply_env_overrides(value, prefix=env_key + "_")
            else:
                env_value = os.environ.get(env_key)
                if env_value is not None:
                    if isinstance(value, bool):
                        env_value = env_value.lower() in ("1", "true", "yes", "on")
                    elif isinstance(value, int):
                        env_value = int(env_value)
                    elif isinstance(value, float):
                        env_value = float(env_value)
                    new_config[key] = env_value
                else:
                    new_config[key] = value
        return new_config

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
