"""Application paths and settings."""

from __future__ import annotations

import sys
from pathlib import Path

from utils.core_functions import get_data_path, is_frozen, project_root, src_root


def find_project_root(marker_filename: str = ".project_root") -> Path:
    if is_frozen():
        return project_root()

    current_path = src_root()
    for parent in [current_path] + list(current_path.parents):
        if (parent / marker_filename).exists():
            return parent

    return current_path.parent


PROJECT_ROOT = find_project_root()
PROJECT_LIB = PROJECT_ROOT / "prod" / "lib"

LOG_BASE_DIR_NAME = "timeLog"
REPORTS_DIR_NAME = "report"
DATABASE_FILE_NAME = "time_tracker_data.sqlite"

LEGACY_LOG_BASE_DIR = PROJECT_LIB / LOG_BASE_DIR_NAME
LEGACY_DATABASE_FILE_PATH = LEGACY_LOG_BASE_DIR / DATABASE_FILE_NAME
LEGACY_REPORTS_DIR_PATH = LEGACY_LOG_BASE_DIR / REPORTS_DIR_NAME

DATA_DIR = get_data_path()
LOG_BASE_DIR = DATA_DIR / LOG_BASE_DIR_NAME
DATABASE_FILE_PATH = LOG_BASE_DIR / DATABASE_FILE_NAME
REPORTS_DIR_PATH = LOG_BASE_DIR / REPORTS_DIR_NAME

ICON_DIR_NAME = "icons"
ICON_DIR_PATH = PROJECT_LIB / ICON_DIR_NAME
TIMER_ICON_NAME = "timer_icon_32.ico"
BARCHART_ICON_NAME = "barchart_32.ico"
RUN_IMAGE_NAME = "play.png"
PAUSE_IMAGE_NAME = "pause.png"

TIMER_ICON_PATH = ICON_DIR_PATH / TIMER_ICON_NAME
BARCHART_ICON_PATH = ICON_DIR_PATH / BARCHART_ICON_NAME
RUN_IMAGE_PATH = ICON_DIR_PATH / RUN_IMAGE_NAME
PAUSE_IMAGE_PATH = ICON_DIR_PATH / PAUSE_IMAGE_NAME

DEFAULT_BREAK_TIME_SECONDS = 3000
MIN_BREAK_TIME_SECONDS = 600


def ensure_directories_exist() -> None:
    dirs_to_create = [
        LOG_BASE_DIR,
        REPORTS_DIR_PATH,
        ICON_DIR_PATH,
    ]
    for dir_path in dirs_to_create:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(f"Error creating directory {dir_path}: {exc}", file=sys.stderr)
