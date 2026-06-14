"""Minimal JSON user preferences (update snooze, etc.)."""

from __future__ import annotations

import json
from typing import Any

from utils.core_functions import get_data_path

CONFIG_FILE = get_data_path() / "app_config.json"


def load_config() -> dict[str, Any]:
    if not CONFIG_FILE.is_file():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict[str, Any]) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
