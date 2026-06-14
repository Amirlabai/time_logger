"""Tests for path helpers."""

from pathlib import Path

from utils.core_functions import asset_file_uri, get_data_path, is_frozen, resource_path, src_root


def test_src_root_exists():
    assert src_root().is_dir()
    assert (src_root() / "web_app.py").exists()


def test_resource_path_web_index():
    path = resource_path("web/index.html")
    assert path.exists()
    assert path.name == "index.html"


def test_asset_file_uri_scheme():
    uri = asset_file_uri("web/index.html")
    assert uri.startswith("file://")


def test_get_data_path_creates_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("utils.core_functions.is_frozen", lambda: False)
    monkeypatch.setattr("utils.core_functions.project_root", lambda: tmp_path)
    data = get_data_path()
    assert data.exists()
    assert data.name == "user_data"
