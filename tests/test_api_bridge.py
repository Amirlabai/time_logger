"""Tests for bridge API without real webview."""

from bridge.api_bridge import TimeTrackerApi


class FakeWindow:
    def evaluate_js(self, js):
        self.last_js = js

    def destroy(self):
        pass


def test_ok_err_envelopes():
    api = TimeTrackerApi()
    assert api._ok()["status"] == "success"
    assert api._ok({"x": 1})["x"] == 1
    assert api._err("fail")["message"] == "fail"


def test_submit_category_without_pending():
    api = TimeTrackerApi()
    api._logger = type("L", (), {"save_program_category_to_db": lambda *a: True})()
    r = api.submit_category("test.exe", "Work")
    assert r["status"] == "error"


def test_emit_event_with_window():
    api = TimeTrackerApi()
    window = FakeWindow()
    api.set_window(window)
    api._emit_event("on_test", {"a": 1})
    assert "on_test" in window.last_js
