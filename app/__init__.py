from app.utils.dotenv_loader import load_env

load_env()

from app.base.config_loader import ConfigLoader
from app.base.logging.logging_setup import logger

config = ConfigLoader()

__all__ = ["config", "logger"]
