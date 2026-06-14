from utils import update_check


def test_is_newer():
    assert update_check._is_newer("0.1.0", "0.2.0")
    assert not update_check._is_newer("1.0.0", "1.0.0")
    assert not update_check._is_newer("2.0.0", "1.9.9")


def test_check_for_update_available_and_skip():
    cfg = {"updates": {"update_check_enabled": True}}
    cfg_skip = {
        "updates": {
            "update_check_enabled": True,
            "update_skip_version": "1.0.0",
        }
    }
    original = update_check.fetch_manifest

    def fake_manifest(_url=""):
        return {
            "version": "1.0.0",
            "installer_url": "https://example.com/setup.exe",
            "release_page": "https://example.com/releases",
            "notes": "Test",
        }

    update_check.fetch_manifest = fake_manifest
    try:
        skipped = update_check.check_for_update("0.1.0", cfg_skip, force=True)
        assert skipped["reason"] == "skipped"

        available = update_check.check_for_update("0.1.0", cfg, force=True)
        assert available["reason"] == "available"
        assert available["latest_version"] == "1.0.0"
    finally:
        update_check.fetch_manifest = original
