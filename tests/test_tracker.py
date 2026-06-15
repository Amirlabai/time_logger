"""Tests for window tracker behavior."""

from models.tracker import WindowTracker


class FakeLogger:
    def log_activity(self, *args, **kwargs):
        pass


def test_ignored_program_does_not_change_active_window(monkeypatch):
    tracker = WindowTracker(FakeLogger(), FakeLogger().log_activity, {})
    tracker.active_window_exe = "chrome"
    tracker.active_window_title = "Example"

    calls = {"count": 0}

    def fake_get_active_window_info():
        calls["count"] += 1
        return "msedgewebview2", "Time Tracker"

    monkeypatch.setattr(tracker, "get_active_window_info", fake_get_active_window_info)
    monkeypatch.setattr("models.tracker.time.sleep", lambda _seconds: None)

    tracker.running = True
    tracker.track_windows = tracker.track_windows.__get__(tracker, WindowTracker)

    original_running = tracker.running

    def one_iteration():
        tracker.running = True
        import models.tracker as tracker_module

        current_exe, _ = tracker.get_active_window_info()
        if current_exe in tracker_module.config.IGNORED_TRACKING_PROGRAMS:
            return
        if current_exe and current_exe != tracker.active_window_exe:
            tracker.active_window_exe = current_exe

    one_iteration()
    assert tracker.active_window_exe == "chrome"
    assert calls["count"] == 1
    tracker.running = original_running
