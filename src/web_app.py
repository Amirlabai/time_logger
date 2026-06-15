"""PyWebView entry point for Time Tracker."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    src_dir = Path(__file__).resolve().parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


def main() -> None:
    _ensure_src_on_path()

    from utils.app_logger import app_logger
    from utils.core_functions import asset_file_uri, is_frozen
    from bridge.api_bridge import TimeTrackerApi

    try:
        import webview
    except ImportError:
        app_logger.exception("pywebview is required. Install with: pip install pywebview")
        raise

    api = TimeTrackerApi()
    app_logger.info("Time Tracker starting (frozen=%s)", is_frozen())

    window = webview.create_window(
        title="Time Tracker",
        url=asset_file_uri("web/index.html"),
        js_api=api,
        width=800,
        height=800,
        min_size=(450, 400),
        text_select=True,
    )
    api.set_window(window)
    webview.start(gui="edgechromium", debug=not is_frozen())


if __name__ == "__main__":
    main()
