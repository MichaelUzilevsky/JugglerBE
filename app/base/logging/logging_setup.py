import logging.config
from pathlib import Path

import yaml

from app.base.logging.context_filter import ContextFilter


def setup_logging():
    """
    Loads logging configuration from YAML and applies custom filters/paths.
    Raises:
        FileNotFoundError: If the logger config file is not found.
    """
    config_path = Path(__file__).resolve().parent.parent.parent / "configs" / "logging" / "logger.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Logger config file not found: {config_path}")

    with open(config_path, "r") as f:
        log_config = yaml.safe_load(f)

    logs_dir = Path(__file__).resolve().parent.parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Replace placeholder in config
    if "handlers" in log_config:
        for handler in log_config.get("handlers", {}).values():
            if isinstance(handler, dict) and "filename" in handler:
                handler["filename"] = str(logs_dir / handler["filename"])

    logging.config.dictConfig(log_config)

    # Add request_id filter to all handlers
    logger = logging.getLogger("app")
    for handler in logger.handlers:
        handler.addFilter(ContextFilter())

    return logger

logger = setup_logging()
