"""PyWebView JavaScript bridge API."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from utils import config
from utils.app_logger import app_logger
from utils.core_functions import asset_file_uri, migrate_legacy_data_if_needed
from utils.db_utils import initialize_database
from models.category_coordinator import CategoryCoordinator
from models.graph_service import GraphService
from models.logger_service import LoggerService
from models.tracker import BreakTimeValidationError, WindowTracker


class TimeTrackerApi:
    def __init__(self) -> None:
        self._window = None
        self._logger: LoggerService | None = None
        self._graph: GraphService | None = None
        self._tracker: WindowTracker | None = None
        self._coordinator = CategoryCoordinator(
            save_default=self._save_default_category,
        )
        self._started = False
        self._initial_category_map: dict[str, str] = {}

    def set_window(self, window) -> None:
        self._window = window
        self._coordinator.set_emit_prompt(self._emit_category_prompt)

    def _ok(self, payload: dict | None = None) -> dict:
        result: dict[str, Any] = {"status": "success"}
        if payload:
            result.update(payload)
        return result

    def _err(self, message: str) -> dict:
        return {"status": "error", "message": str(message)}

    def _emit_event(self, handler: str, payload: dict) -> None:
        if not self._window:
            return
        try:
            js = f"if (window.{handler}) window.{handler}({json.dumps(payload)});"
            self._window.evaluate_js(js)
        except Exception:
            app_logger.debug(f"Failed to emit JS event {handler}", exc_info=True)

    def _emit_category_prompt(self, program_name: str) -> None:
        self._emit_event(
            "on_category_prompt",
            {"program": program_name, "categories": self._logger.get_CATEGORIES() if self._logger else []},
        )

    def _save_default_category(self, program_name: str, category: str) -> None:
        if self._logger:
            self._logger.save_program_category_to_db(program_name, category)

    def prepare_startup(self) -> dict:
        try:
            migrate_legacy_data_if_needed(
                config.LEGACY_DATABASE_FILE_PATH,
                config.DATABASE_FILE_PATH,
            )
            config.ensure_directories_exist()
            initialize_database()
            self._logger = LoggerService()
            self._graph = GraphService(self._logger)
            self._initial_category_map = dict(self._logger.category_map)
            self._tracker = WindowTracker(
                self._logger,
                self._logger.log_activity,
                self._logger.category_map,
                category_callback=self._coordinator.request_category,
            )
            self._tracker.start_tracking()
            self._started = True
            app_logger.info("Startup completed successfully.")
            return self._ok()
        except Exception as exc:
            app_logger.critical(f"Startup failed: {exc}", exc_info=True)
            return self._err(str(exc))

    def get_initial_data(self) -> dict:
        if not self._logger or not self._tracker:
            return self._err("Application not initialized")
        return self._ok(
            {
                "categories_summary": self._logger.get_category_summary(),
                "category_names": self._logger.get_CATEGORIES(),
                "program_categories": self._logger.get_program_categories(),
                "break_interval_minutes": self._tracker.break_interval_minutes,
                "min_break_minutes": config.MIN_BREAK_TIME_SECONDS // 60,
                "run_icon_uri": self._icon_uri(config.RUN_IMAGE_PATH),
                "pause_icon_uri": self._icon_uri(config.PAUSE_IMAGE_PATH),
                "play_icon_uri": self._icon_uri(config.RUN_IMAGE_PATH),
            }
        )

    def _icon_uri(self, path: Path) -> str:
        if path.exists():
            return path.resolve().as_uri()
        return ""

    def get_dashboard_state(self) -> dict:
        if not self._tracker or not self._logger:
            return self._err("Application not initialized")
        state = self._tracker.get_dashboard_state()
        if state.pop("break_reminder", False):
            self._emit_event("on_break_reminder", {"message": "It's time to take a break."})
            self._tracker.reset_break_timer_countdown()
            self._tracker.set_break_timer_running(True)
        return self._ok(
            {
                **state,
                "categories_summary": self._logger.get_category_summary(),
            }
        )

    def set_break_interval(self, minutes: int) -> dict:
        if not self._tracker:
            return self._err("Tracker not initialized")
        try:
            self._tracker.set_break_interval_minutes(int(minutes))
            return self._ok({"break_interval_display": self._tracker.break_time_setting_display})
        except BreakTimeValidationError as exc:
            return self._err(str(exc))
        except (TypeError, ValueError):
            return self._err("Enter a valid number of minutes.")

    def reset_break_countdown(self) -> dict:
        if not self._tracker:
            return self._err("Tracker not initialized")
        self._tracker.reset_break_timer_countdown()
        return self._ok({"break_countdown_display": self._tracker.break_time_counter_display})

    def toggle_break_timer(self, running: bool) -> dict:
        if not self._tracker:
            return self._err("Tracker not initialized")
        try:
            self._tracker.set_break_timer_running(bool(running))
            return self._ok({"break_timer_running": self._tracker.is_running_break_time})
        except BreakTimeValidationError as exc:
            return self._err(str(exc))

    def get_program_categories(self) -> dict:
        if not self._logger:
            return self._err("Logger not initialized")
        return self._ok(
            {
                "program_categories": self._logger.get_program_categories(),
                "category_names": self._logger.get_CATEGORIES(),
            }
        )

    def save_program_categories(self, payload: dict) -> dict:
        if not self._logger:
            return self._err("Logger not initialized")
        categories = payload.get("categories") or {}
        update_historical = bool(payload.get("update_historical", False))
        if not isinstance(categories, dict):
            return self._err("Invalid categories payload")

        saved = self._logger.save_program_categories_batch(categories)
        if update_historical:
            for program_name, new_category in categories.items():
                original = self._initial_category_map.get(program_name)
                if original != new_category:
                    self._logger.update_categories_in_log_entries(
                        program_name, new_category
                    )
        self._initial_category_map = dict(self._logger.category_map)
        return self._ok({"saved_count": saved})

    def submit_category(self, program: str, category: str) -> dict:
        if not program:
            return self._err("Program name required")
        final_category = (category or "Misc").strip().title() or "Misc"
        if self._logger:
            if not self._logger.save_program_category_to_db(program, final_category):
                return self._err("Could not save category to database.")
            if self._tracker:
                self._tracker.category_map[program] = final_category
        if not self._coordinator.submit_category(program, final_category):
            return self._err("No pending category request for this program.")
        return self._ok({"category": final_category})

    def dismiss_category(self, program: str) -> dict:
        if self._logger:
            self._logger.save_program_category_to_db(program, "Misc")
            if self._tracker:
                self._tracker.category_map[program] = "Misc"
        self._coordinator.dismiss_category(program)
        return self._ok({"category": "Misc"})

    def graph_get_data(self, filter_category: str = "All Categories") -> dict:
        if not self._graph:
            return self._err("Graph service not initialized")
        result = self._graph.get_graph_data(filter_category or "All Categories")
        if result.get("status") == "error":
            return self._err(result.get("message", "Graph error"))
        return result

    def pick_save_path(self, initial_dir: str = "", default_name: str = "activity_report.csv") -> dict:
        if not self._window:
            return self._err("Window not ready")
        try:
            import webview

            directory = initial_dir or str(config.REPORTS_DIR_PATH)
            if not os.path.isdir(directory):
                directory = str(config.LOG_BASE_DIR)
            result = self._window.create_file_dialog(
                webview.SAVE_DIALOG,
                directory=directory,
                save_filename=default_name,
                file_types=("CSV files (*.csv)", "All files (*.*)"),
            )
            if not result:
                return self._ok({"path": "", "cancelled": True})
            path = result if isinstance(result, str) else result[0]
            return self._ok({"path": path, "cancelled": False})
        except Exception as exc:
            app_logger.error("pick_save_path failed", exc_info=True)
            return self._err(str(exc))

    def export_report(self, payload: dict) -> dict:
        if not self._logger:
            return self._err("Logger not initialized")
        file_path = payload.get("path", "")
        export_type = payload.get("export_type", "all")
        start_date = payload.get("start_date")
        end_date = payload.get("end_date")
        if not file_path:
            return self._err("No file path provided")
        try:
            self._logger.export_to_csv(file_path, export_type, start_date, end_date)
            return self._ok({"path": file_path})
        except ValueError as exc:
            return self._err(str(exc))
        except Exception as exc:
            app_logger.error("export_report failed", exc_info=True)
            return self._err(str(exc))

    def log_js(self, message: str) -> dict:
        app_logger.warning(f"JS: {message}")
        return self._ok()

    def exit_app(self) -> dict:
        if self._tracker:
            self._tracker.stop_tracking()
        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass
        return self._ok()
