"""Unit tests for clickbot.paths module."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from clickbot import paths


class TestIsFrozen:
    """Tests for is_frozen()."""

    def test_not_frozen_in_dev_mode(self) -> None:
        """is_frozen() returns False when running from source."""
        assert paths.is_frozen() is False

    def test_frozen_when_sys_frozen(self) -> None:
        """is_frozen() returns True when sys.frozen and sys._MEIPASS are set."""
        with patch.object(sys, 'frozen', True, create=True):
            with patch.object(sys, '_MEIPASS', 'C:\\temp\\_MEI123', create=True):
                assert paths.is_frozen() is True

    def test_not_frozen_without_meipass(self) -> None:
        """is_frozen() returns False if sys.frozen but no _MEIPASS."""
        with patch.object(sys, 'frozen', True, create=True):
            # Remove _MEIPASS if it exists
            if hasattr(sys, '_MEIPASS'):
                with patch.object(sys, '_MEIPASS', None, create=True):
                    # hasattr check fails because _MEIPASS is None but exists
                    pass
            assert paths.is_frozen() is False


class TestGetBundleDir:
    """Tests for get_bundle_dir()."""

    def test_dev_mode_returns_project_root(self) -> None:
        """In dev mode, bundle dir is the project root."""
        bundle_dir = paths.get_bundle_dir()
        # Should be the parent of the clickbot package
        assert (bundle_dir / "clickbot").is_dir()
        assert (bundle_dir / "config").is_dir()

    def test_frozen_mode_returns_meipass(self) -> None:
        """In frozen mode, bundle dir is sys._MEIPASS."""
        fake_meipass = "C:\\temp\\_MEI12345"
        with patch.object(sys, 'frozen', True, create=True):
            with patch.object(sys, '_MEIPASS', fake_meipass, create=True):
                assert paths.get_bundle_dir() == Path(fake_meipass)


class TestGetUserDataDir:
    """Tests for get_user_data_dir()."""

    def test_dev_mode_returns_project_root(self) -> None:
        """In dev mode, user data dir is the project root."""
        data_dir = paths.get_user_data_dir()
        assert data_dir == paths.get_bundle_dir()

    def test_frozen_mode_returns_appdata(self) -> None:
        """In frozen mode, user data dir is %APPDATA%/TaxActBot."""
        with patch.object(sys, 'frozen', True, create=True):
            with patch.object(sys, '_MEIPASS', 'C:\\temp\\_MEI', create=True):
                with patch.dict(os.environ, {"APPDATA": "C:\\Users\\test\\AppData\\Roaming"}):
                    with patch.object(Path, 'mkdir'):
                        data_dir = paths.get_user_data_dir()
                        assert data_dir == Path("C:\\Users\\test\\AppData\\Roaming\\TaxActBot")


class TestConvenienceFunctions:
    """Tests for convenience path functions."""

    def test_get_settings_path(self) -> None:
        """Settings path is under user data dir."""
        settings = paths.get_settings_path()
        assert settings.name == "settings.json"
        assert "config" in settings.parts

    def test_get_default_settings_path(self) -> None:
        """Default settings path is under bundle dir."""
        default = paths.get_default_settings_path()
        assert default.name == "settings.json"
        assert default.exists()  # Should exist in dev mode

    def test_get_processes_dir(self) -> None:
        """Processes dir exists and contains JSON files."""
        proc_dir = paths.get_processes_dir()
        assert proc_dir.is_dir()
        json_files = list(proc_dir.glob("*.json"))
        assert len(json_files) >= 2  # 1120.json, 1120S.json

    def test_get_log_dir_creates_dir(self) -> None:
        """get_log_dir() creates the directory if needed."""
        log_dir = paths.get_log_dir()
        assert log_dir.is_dir()

    def test_get_assets_dir(self) -> None:
        """Assets dir points to correct location."""
        assets = paths.get_assets_dir()
        assert "assets" in str(assets)

    def test_get_buttons_dir(self) -> None:
        """Buttons dir points to screenshot templates."""
        buttons = paths.get_buttons_dir()
        assert buttons.is_dir()
        assert (buttons / "common").is_dir()

    def test_get_tesseract_path(self) -> None:
        """Tesseract path points to bundle location."""
        tess = paths.get_tesseract_path()
        assert tess.name == "tesseract.exe"
        assert "tesseract_bundle" in str(tess)


class TestEnsureUserConfig:
    """Tests for ensure_user_config()."""

    def test_dev_mode_returns_existing_config(self) -> None:
        """In dev mode, returns the existing config path (same as default)."""
        config = paths.ensure_user_config()
        assert config.exists()
        assert config.name == "settings.json"
