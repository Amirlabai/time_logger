"""Path helpers for dev vs frozen PyInstaller builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def src_root() -> Path:
    return Path(__file__).resolve().parent.parent


def project_root() -> Path:
    if is_frozen():
        return Path(sys._MEIPASS).resolve()
    return src_root().parent


def resource_path(relative_path: str) -> Path:
    if is_frozen():
        return Path(sys._MEIPASS) / relative_path
    return src_root() / relative_path


def get_data_path() -> Path:
    if is_frozen():
        base = Path(os.environ.get("APPDATA", str(Path.home()))) / "TimeTracker"
    else:
        base = project_root() / "user_data"
    base.mkdir(parents=True, exist_ok=True)
    return base


def asset_file_uri(relative_path: str) -> str:
    path = resource_path(relative_path).resolve()
    return path.as_uri()


def migrate_legacy_data_if_needed(legacy_db_path: Path, target_db_path: Path) -> None:
    """Copy SQLite from legacy dev location on first run after migration."""
    if target_db_path.exists() or not legacy_db_path.exists():
        return
    target_db_path.parent.mkdir(parents=True, exist_ok=True)
    import shutil

    shutil.copy2(legacy_db_path, target_db_path)
