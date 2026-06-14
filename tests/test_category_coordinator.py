"""Tests for category prompt coordination."""

import threading
import time

from models.category_coordinator import CategoryCoordinator


def test_submit_category_resolves_waiter():
    coordinator = CategoryCoordinator(timeout_seconds=5)
    results = {}

    def worker():
        results["category"] = coordinator.request_category("notepad.exe")

    thread = threading.Thread(target=worker)
    thread.start()
    time.sleep(0.05)
    assert coordinator.submit_category("notepad.exe", "Work")
    thread.join(timeout=2)
    assert results["category"] == "Work"


def test_timeout_returns_misc():
    coordinator = CategoryCoordinator(timeout_seconds=0.2, save_default=lambda p, c: None)
    category = coordinator.request_category("unknown.exe")
    assert category == "Misc"


def test_dismiss_uses_misc():
    coordinator = CategoryCoordinator(timeout_seconds=5)
    saved = {}

    def save_default(prog, cat):
        saved[prog] = cat

    coordinator._save_default = save_default

    def worker():
        saved["result"] = coordinator.request_category("app.exe")

    thread = threading.Thread(target=worker)
    thread.start()
    time.sleep(0.05)
    coordinator.dismiss_category("app.exe")
    thread.join(timeout=2)
    assert saved["result"] == "Misc"
    assert saved["app.exe"] == "Misc"
