import logging
import logging.config
import yaml
from pathlib import Path


def setup_logging():
    config_path = Path(__file__).resolve().parent.parent.parent / "configs" / "logging" / "logger.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Logger config file not found: {config_path}")

    with open(config_path, "r") as f:
        log_config = yaml.safe_load(f)

    logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Replace placeholder in config
    if "handlers" in log_config:
        for handler in log_config["handlers"].values():
            if isinstance(handler, dict) and "filename" in handler:
                handler["filename"] = str(logs_dir / handler["filename"])

    logging.config.dictConfig(log_config)


# Initialize and expose global logger
setup_logging()
logger = logging.getLogger("src")
