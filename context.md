# Time Tracker — context

## Purpose

Windows desktop app that tracks foreground window usage, assigns categories to programs, logs sessions to SQLite, shows usage graphs, and exports CSV reports.

## Architecture (v2 — PyWebView)

```
src/web_app.py          → webview.create_window + webview.start
src/bridge/api_bridge.py → TimeTrackerApi (JS-callable methods)
src/web/*               → HTML/CSS/JS UI (Chart.js for graphs)
src/models/             → LoggerService, GraphService, WindowTracker, CategoryCoordinator
src/utils/              → config, db_utils, core_functions, app_logger
```

Python owns: SQLite, window tracking (pywin32/psutil), native save dialog, background tracker thread.

HTML/JS owns: dashboard, modals, Chart.js graphs, 1s polling via `get_dashboard_state()`.

Category prompts: tracker thread blocks on `CategoryCoordinator`; bridge pushes `on_category_prompt` to JS; JS calls `submit_category()`.

## Key paths

| Item | Dev | Frozen |
|------|-----|--------|
| Database | `user_data/timeLog/time_tracker_data.sqlite` | `%APPDATA%/TimeTracker/timeLog/` |
| Logs | `user_data/time_tracker_app.log` | `%APPDATA%/TimeTracker/` |
| Web assets | `src/web/` | bundled in `_MEIPASS/web/` |
| Icons | `prod/lib/icons/` | bundled with exe |

Legacy DB at `prod/lib/timeLog/` is copied on first startup if the new path is empty.

## Entry points

- GUI: `python src/web_app.py`
- CLI: `python src/cli.py init-db` / `export`
- Deprecated: `python prod/code/main.py` (prints redirect)

## Dependencies

pywebview, pandas, psutil, pywin32 (Windows only).

## Packaging

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe prod\gen_exe.py
```

Output: `prod/installers/TimeTracker_Setup_<version>.exe` (version from `pyproject.toml`).

Scripts: `prod/gen_exe.py` (PyInstaller + Inno), `prod/create_installer.iss`.

Requires Inno Setup 6 (`ISCC.exe`) or set `INNO_SETUP_PATH`.

## Conventions

- Bridge methods return `{status: "success"|"error", ...}`
- Wait for `pywebviewready` before API calls
- No Tkinter in new code path
