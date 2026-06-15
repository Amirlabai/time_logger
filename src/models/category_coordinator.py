"""Thread-safe category prompt coordination for background tracker."""

from __future__ import annotations

import threading
from typing import Callable

from utils.app_logger import app_logger


class CategoryCoordinator:
    def __init__(
        self,
        save_default: Callable[[str, str], None] | None = None,
        timeout_seconds: float = 300,
    ) -> None:
        self._save_default = save_default
        self._timeout = timeout_seconds
        self._pending: dict[str, tuple[threading.Event, dict[str, str]]] = {}
        self._ui_prompt_program: str | None = None
        self._ui_prompt_sent = False
        self._lock = threading.Lock()

    def request_category(self, program_name: str) -> str:
        """Queue a UI prompt and return Misc immediately (tracker must not block)."""
        with self._lock:
            if program_name in self._pending:
                return "Misc"
            self._pending[program_name] = (threading.Event(), {"category": "Misc"})
            self._ui_prompt_program = program_name
            self._ui_prompt_sent = False
        app_logger.info(f"Queued category prompt for '{program_name}'.")
        return "Misc"

    def take_ui_prompt(self) -> str | None:
        """Return a program that needs a UI prompt; safe to call from the webview thread."""
        with self._lock:
            if self._ui_prompt_program and not self._ui_prompt_sent:
                self._ui_prompt_sent = True
                return self._ui_prompt_program
            return None

    def submit_category(self, program_name: str, category: str) -> bool:
        with self._lock:
            pending = self._pending.pop(program_name, None)
            if not pending:
                return False
            self._clear_ui_prompt_locked(program_name)
        _event, result_dict = pending
        result_dict["category"] = category or "Misc"
        _event.set()
        return True

    def dismiss_category(self, program_name: str) -> bool:
        if self._save_default:
            self._save_default(program_name, "Misc")
        return self.submit_category(program_name, "Misc")

    def has_pending(self, program_name: str) -> bool:
        with self._lock:
            return program_name in self._pending

    def _clear_ui_prompt_locked(self, program_name: str) -> None:
        if self._ui_prompt_program == program_name:
            self._ui_prompt_program = None
            self._ui_prompt_sent = False
