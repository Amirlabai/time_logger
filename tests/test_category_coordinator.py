"""Tests for category prompt coordination."""

from models.category_coordinator import CategoryCoordinator


def test_request_category_queues_prompt():
    coordinator = CategoryCoordinator()
    assert coordinator.request_category("notepad.exe") == "Misc"
    assert coordinator.take_ui_prompt() == "notepad.exe"
    assert coordinator.take_ui_prompt() is None
    assert coordinator.submit_category("notepad.exe", "Work")
    assert not coordinator.has_pending("notepad.exe")


def test_duplicate_request_is_idempotent():
    coordinator = CategoryCoordinator()
    assert coordinator.request_category("unknown.exe") == "Misc"
    assert coordinator.request_category("unknown.exe") == "Misc"
    assert coordinator.take_ui_prompt() == "unknown.exe"


def test_dismiss_uses_misc():
    coordinator = CategoryCoordinator()
    saved = {}

    def save_default(prog, cat):
        saved[prog] = cat

    coordinator._save_default = save_default
    coordinator.request_category("app.exe")
    coordinator.dismiss_category("app.exe")
    assert saved["app.exe"] == "Misc"
    assert not coordinator.has_pending("app.exe")
