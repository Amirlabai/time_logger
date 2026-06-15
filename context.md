# Time Tracker — context

## Purpose

Windows desktop app that tracks foreground window usage, assigns categories to programs, logs sessions to SQLite, shows usage graphs, and exports CSV reports.

## Architecture (v2 — PyWebView)

```
src/web_app.py          → webview.create_window + webview.start
src/bridge/api_bridge.py → TimeTrackerApi (JS-callable methods)
src/web/*               → HTML/CSS/JS UI (Chart.js 4.4.1 vendored at web/vendor/chart.umd.min.js)
src/models/             → LoggerService, GraphService, WindowTracker, CategoryCoordinator
src/utils/              → config, db_utils, core_functions, app_logger
```

Python owns: SQLite, window tracking (pywin32/psutil), native save dialog, background tracker thread.

HTML/JS owns: dashboard, modals, Chart.js graphs, 1s polling via `get_dashboard_state()`.

Category prompts: tracker queues a prompt via `CategoryCoordinator` (non-blocking, provisional `Misc`); `get_dashboard_state()` returns `category_prompt` via `peek_ui_prompt()` on each poll until submit/dismiss. JS defers prompt with `setTimeout(0)` and skips when `isModalOpen()` so another modal can finish first. No `evaluate_js` or window lift from API handlers. Foreground `msedgewebview2` / `python` / `TimeTracker` are ignored (`config.IGNORED_TRACKING_PROGRAMS`).

Update checks: `latest.json` on main; **Check for Updates** in header; startup poll (24h throttle) via `utils/update_check.py`.

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

Local build:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe prod\gen_exe.py
```

CI release pipeline (same pattern as Video-Editor):

1. Push to `main` with Conventional Commits → **Semantic Release** bumps `pyproject.toml`, tags `vX.Y.Z`, creates GitHub Release.
2. **Build and Release Installer** runs after Semantic Release → Windows build → uploads `TimeTracker_Setup_X.Y.Z.exe` to that tag.

Backfill an existing tag: Actions → **Build and Release Installer** → Run workflow → version `X.Y.Z`.

Workflows: `.github/workflows/release.yml`, `.github/workflows/release-installer.yml`.

Requires Inno Setup 6 locally (`INNO_SETUP_PATH`) or use CI.

## Conventions

- Bridge methods return `{status: "success"|"error", ...}`
- Wait for `pywebviewready` before API calls
- Shared UI: `showModal` (with `onOpen`, `initialFocus`), `showAlert`, `showLoading`, `escapeHtml`, `isModalOpen` in `app.js`
- Blocking coordinator: `acquireBlocking` / `releaseBlocking` in `app.js` — modal + loading share `aria-hidden` on `#app` and unified focus trap (loading layer wins when both active); `#alert-region` sits outside `#app` (z-index above loading)
- Loading overlay: `role="alertdialog"`, `aria-labelledby="loading-message"` per ui-protocols loading contract
- No Tkinter in new code path
