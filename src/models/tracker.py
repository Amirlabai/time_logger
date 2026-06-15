"""Background window tracking (Windows only)."""

from __future__ import annotations

import threading
import time
from typing import Callable

import psutil

from utils import config
from utils.app_logger import app_logger


class BreakTimeValidationError(ValueError):
    pass


class WindowTracker:
    def __init__(
        self,
        logger_instance,
        log_activity_callback: Callable,
        category_map: dict,
        break_time_seconds: int | None = None,
        category_callback: Callable[[str], str] | None = None,
    ) -> None:
        self.logger_instance = logger_instance
        self.log_activity = log_activity_callback
        self.category_map = category_map
        self.category_callback = category_callback
        self.running = True
        self.active_window_exe: str | None = None
        self.active_window_title: str | None = None
        self.run_break_time = False
        self.current_session_total_time_seconds = 0.0

        if break_time_seconds is None:
            self._break_time = config.DEFAULT_BREAK_TIME_SECONDS
        else:
            self._break_time = max(config.MIN_BREAK_TIME_SECONDS, break_time_seconds)

        self._break_time_counter_seconds = float(self._break_time)
        self.current_session_start_time_epoch = time.time()
        self._break_timer_absolute_start_epoch = time.time()
        self.previous_window_exe: str | None = None
        self.thread: threading.Thread | None = None
        self._break_message_pending = False

        app_logger.info("WindowTracker initialized.")

    @property
    def break_time_counter_display(self) -> str:
        time_frame = int(self._break_time_counter_seconds)
        hours, remainder = divmod(time_frame, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    @property
    def is_running_break_time(self) -> bool:
        return self.run_break_time

    @property
    def is_running(self) -> bool:
        return self.running

    @property
    def break_time_setting_display(self) -> str:
        time_frame = int(self._break_time)
        hours, remainder = divmod(time_frame, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    @property
    def break_interval_minutes(self) -> int:
        return self._break_time // 60

    def set_break_interval_minutes(self, minutes: int) -> None:
        total_seconds = int(minutes) * 60
        if total_seconds < config.MIN_BREAK_TIME_SECONDS:
            raise BreakTimeValidationError(
                f"Break time must be at least {config.MIN_BREAK_TIME_SECONDS // 60} minutes."
            )
        self._break_time = total_seconds
        self._break_timer_absolute_start_epoch = time.time()
        self._break_time_counter_seconds = float(self._break_time)
        app_logger.info(f"Break time setting updated to {total_seconds} seconds.")

    def set_break_timer_running(self, flag: bool) -> None:
        if not isinstance(flag, bool):
            raise BreakTimeValidationError("Break timer flag must be boolean.")
        self.run_break_time = flag
        if flag:
            app_logger.info("Break time started")
            self._break_timer_absolute_start_epoch = time.time() - (
                self._break_time - self._break_time_counter_seconds
            )
        else:
            app_logger.info("Break time stopped")

    def reset_break_timer_countdown(self) -> None:
        self._break_timer_absolute_start_epoch = time.time()
        self._break_time_counter_seconds = float(self._break_time)
        self._break_message_pending = False
        app_logger.info("Break timer countdown reset.")

    def get_active_window_info(self) -> tuple[str, str]:
        try:
            import win32gui
            import win32process

            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                return "Idle", "No Active Window"
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == 0:
                return "UnknownProcess", "Unknown Window (PID 0)"
            process = psutil.Process(pid)
            app_name = process.name().replace(".exe", "")
            window_title = win32gui.GetWindowText(hwnd)
            if not window_title:
                window_title = app_name
            return app_name, window_title
        except ImportError:
            app_logger.error("pywin32 is required for window tracking on Windows")
            return "Unknown", "pywin32 not available"
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return "Unknown", "Error Accessing Window"
        except Exception:
            app_logger.error("Unexpected error in get_active_window_info", exc_info=True)
            return "Unknown", "Error Fetching Window"

    def should_take_break(self) -> bool:
        return self._break_time_counter_seconds < 0

    def consume_break_reminder(self) -> bool:
        if self.should_take_break() and not self._break_message_pending:
            self._break_message_pending = True
            return True
        if not self.should_take_break():
            self._break_message_pending = False
        return False

    def track_windows(self) -> None:
        app_logger.info("Window tracking thread started.")
        while self.running:
            current_time_epoch = time.time()
            if self.run_break_time:
                self._break_time_counter_seconds = self._break_time - (
                    current_time_epoch - self._break_timer_absolute_start_epoch
                )

            current_exe, current_title = self.get_active_window_info()

            if current_exe in config.IGNORED_TRACKING_PROGRAMS:
                time.sleep(1)
                continue

            if current_exe and current_exe != self.active_window_exe:
                app_logger.debug(
                    f"Window changed from '{self.active_window_exe}' to '{current_exe}'."
                )
                if self.active_window_exe:
                    self.log_activity_for_current_window(self.active_window_title or "")

                self.previous_window_exe = self.active_window_exe
                self.active_window_exe = current_exe
                self.active_window_title = current_title
                self.current_session_start_time_epoch = current_time_epoch
                self.current_session_total_time_seconds = 0

                if (
                    current_exe not in self.category_map
                    and current_exe not in ("Unknown", "Idle")
                ):
                    app_logger.info(
                        f"Program '{current_exe}' not in category map. Requesting category."
                    )
                    category = self._request_category(current_exe)
                    self.category_map[current_exe] = category
                    app_logger.info(
                        f"Program '{current_exe}' assigned to '{category}'."
                    )

            if self.active_window_exe:
                self.current_session_total_time_seconds = (
                    current_time_epoch - self.current_session_start_time_epoch
                )

            time.sleep(1)

        if self.active_window_exe:
            self.log_activity_for_current_window(self.active_window_title or "")
        app_logger.info("Window tracking thread stopped.")

    def _request_category(self, program_name: str) -> str:
        if self.category_callback:
            return self.category_callback(program_name)
        return "Misc"

    def log_activity_for_current_window(self, window_title_to_log: str) -> None:
        if not self.active_window_exe:
            return
        end_time_epoch = time.time()
        duration_seconds = end_time_epoch - self.current_session_start_time_epoch
        if duration_seconds < 0.5:
            app_logger.debug(
                f"Skipping log for '{self.active_window_exe}': duration too short."
            )
            return
        self.log_activity(
            self.active_window_exe,
            window_title_to_log,
            self.current_session_start_time_epoch,
            end_time_epoch,
            duration_seconds,
        )

    def start_tracking(self) -> None:
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self.track_windows, daemon=True)
            self.thread.start()
            app_logger.info("Tracking thread started.")
        else:
            app_logger.warning("Tracking thread already running.")

    def stop_tracking(self) -> None:
        app_logger.info("stop_tracking called.")
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                app_logger.warning("Tracking thread did not finish in time.")
        self.thread = None

    def get_dashboard_state(self) -> dict:
        active_exe = self.active_window_exe or "None"
        active_title = self.active_window_title or ""
        if len(active_title) > 60:
            active_title = active_title[:57] + "..."
        seconds = int(self.current_session_total_time_seconds)
        hours, rem = divmod(seconds, 3600)
        minutes, secs = divmod(rem, 60)
        return {
            "current_app_time": f"{hours:02}:{minutes:02}:{secs:02}",
            "active_window": f"{active_exe} - {active_title}" if active_title else active_exe,
            "previous_window": self.previous_window_exe or "None",
            "break_interval_display": self.break_time_setting_display,
            "break_countdown_display": self.break_time_counter_display,
            "break_timer_running": self.run_break_time,
            "break_reminder": self.consume_break_reminder(),
        }
