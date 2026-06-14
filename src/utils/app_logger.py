"""Application-wide logging."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from utils.core_functions import get_data_path


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("TimeTrackerApp")
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_file_path = get_data_path() / "time_tracker_app.log"
    try:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=1024 * 1024 * 5, backupCount=2
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as exc:
        logger.error(f"Failed to set up file handler for logging: {exc}", exc_info=True)

    return logger


app_logger = setup_logger()
