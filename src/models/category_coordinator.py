"""Thread-safe category prompt coordination for background tracker."""

from __future__ import annotations

import threading
from typing import Callable

from utils.app_logger import app_logger


class CategoryCoordinator:
    def __init__(
        self,
        emit_prompt: Callable[[str], None] | None = None,
        save_default: Callable[[str, str], None] | None = None,
        timeout_seconds: float = 300,
    ) -> None:
        self._emit_prompt = emit_prompt
        self._save_default = save_default
        self._timeout = timeout_seconds
        self._pending: dict[str, tuple[threading.Event, dict[str, str]]] = {}
        self._lock = threading.Lock()

    def set_emit_prompt(self, emit_prompt: Callable[[str], None]) -> None:
        self._emit_prompt = emit_prompt

    def request_category(self, program_name: str) -> str:
        result_event = threading.Event()
        result_dict: dict[str, str] = {"category": "Misc"}

        with self._lock:
            self._pending[program_name] = (result_event, result_dict)

        if self._emit_prompt:
            try:
                self._emit_prompt(program_name)
            except Exception:
                app_logger.error(
                    f"Failed to emit category prompt for '{program_name}'",
                    exc_info=True,
                )

        if result_event.wait(timeout=self._timeout):
            category = result_dict["category"]
            with self._lock:
                self._pending.pop(program_name, None)
            return category

        app_logger.warning(
            f"Timeout waiting for category for '{program_name}'. Using 'Misc'."
        )
        with self._lock:
            self._pending.pop(program_name, None)
        if self._save_default:
            self._save_default(program_name, "Misc")
        return "Misc"

    def submit_category(self, program_name: str, category: str) -> bool:
        with self._lock:
            pending = self._pending.get(program_name)
        if not pending:
            return False
        event, result_dict = pending
        result_dict["category"] = category or "Misc"
        event.set()
        return True

    def dismiss_category(self, program_name: str) -> bool:
        if self._save_default:
            self._save_default(program_name, "Misc")
        return self.submit_category(program_name, "Misc")

    def has_pending(self, program_name: str) -> bool:
        with self._lock:
            return program_name in self._pending
