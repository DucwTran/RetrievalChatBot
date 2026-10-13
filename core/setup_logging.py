import logging
import logging.config
from pathlib import Path

import yaml

from core.config import get_settings

LOGGING_CONFIG = Path("config/logging.yaml")
LOG_DIR = Path("logs")  # git-ignored, so it does not exist on a fresh clone


def setup_logging() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    with open(LOGGING_CONFIG, "r", encoding="utf-8") as file:
        logging.config.dictConfig(yaml.safe_load(file))
    logging.getLogger().setLevel(get_settings().log_level.upper())
