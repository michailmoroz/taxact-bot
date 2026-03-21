"""Centralized path resolution for both dev and bundled (PyInstaller) mode.

In dev mode: all paths resolve relative to the project root.
In exe mode: read-only assets come from sys._MEIPASS (bundle dir),
             user-writable files go to %APPDATA%/TaxActBot/.
"""

import logging
import os
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def is_frozen() -> bool:
    """Check if running as PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_bundle_dir() -> Path:
    """Get the base directory for bundled read-only assets.

    In dev mode: project root (parent of clickbot/ package)
    In exe mode: sys._MEIPASS (temp extraction dir with bundled files)
    """
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_user_data_dir() -> Path:
    """Get the user-writable data directory.

    In dev mode: project root (same as bundle dir)
    In exe mode: %APPDATA%/TaxActBot/
    """
    if is_frozen():
        appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        data_dir = appdata / "TaxActBot"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    return Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Convenience functions for specific paths
# ---------------------------------------------------------------------------

def get_settings_path() -> Path:
    """Path to settings.json (always next to the exe / in project root).

    Both dev and exe mode use the same location: bundle_dir/config/settings.json.
    This ensures edits to config/settings.json take effect immediately
    without needing to delete a stale AppData copy.
    """
    return get_bundle_dir() / "config" / "settings.json"


def get_processes_dir() -> Path:
    """Path to process definition JSONs (read-only, bundled)."""
    return get_bundle_dir() / "config" / "processes"


def get_log_dir() -> Path:
    """Path to log directory (user-writable)."""
    log_dir = get_user_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_csv_dir() -> Path:
    """Path to preprocessing CSV output directory."""
    csv_dir = Path("C:/TaxActBot/logs")
    csv_dir.mkdir(parents=True, exist_ok=True)
    return csv_dir


def get_assets_dir() -> Path:
    """Path to assets/ directory (read-only, bundled)."""
    return get_bundle_dir() / "assets"


def get_buttons_dir() -> Path:
    """Path to button template screenshots (read-only, bundled)."""
    return get_bundle_dir() / ".agents" / "screenshots" / "buttons"


def get_tesseract_path() -> Path:
    """Path to bundled tesseract.exe (only meaningful when frozen)."""
    return get_bundle_dir() / "tesseract_bundle" / "tesseract.exe"


def ensure_user_config() -> Path:
    """Return path to settings.json, verifying it exists.

    Returns:
        Path to settings.json (next to exe / in project root)
    """
    settings = get_settings_path()
    if not settings.exists():
        logger.warning(f"Settings not found: {settings}")
    return settings
