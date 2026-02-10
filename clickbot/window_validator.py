"""TaxAct window detection and monitor validation.

Validates that:
- TaxAct is running and visible
- TaxAct window is on the primary monitor (x < 1920)
- Screen resolution matches expected (1920x1080)
"""

import logging
from typing import Optional, Tuple, Any

import pyautogui
import pygetwindow as gw

logger = logging.getLogger(__name__)


def find_taxact_window(title: str = "TaxAct") -> Optional[Any]:
    """Find the TaxAct window by title.

    Args:
        title: Window title to search for. Default "TaxAct".

    Returns:
        Window object if found, None otherwise
    """
    try:
        windows = gw.getWindowsWithTitle(title)

        if not windows:
            logger.warning(f"No window found with title containing '{title}'")
            return None

        # Return the first matching window
        window = windows[0]
        logger.info(f"Found TaxAct window: '{window.title}' at ({window.left}, {window.top})")
        return window

    except Exception as e:
        logger.error(f"Error searching for TaxAct window: {e}")
        return None


def is_on_primary_monitor(window: Any, max_x: int = 1920) -> bool:
    """Check if a window is on the primary monitor.

    Assumes primary monitor starts at x=0 and has width of max_x.
    Window is on primary if its left edge is less than max_x.

    Args:
        window: Window object from PyGetWindow
        max_x: Maximum x coordinate for primary monitor. Default 1920.

    Returns:
        True if window is on primary monitor, False otherwise
    """
    if window is None:
        logger.warning("Cannot check monitor position: window is None")
        return False

    try:
        window_x = window.left

        if window_x >= max_x:
            logger.warning(
                f"Window is on secondary monitor: x={window_x} (>= {max_x})"
            )
            return False

        if window_x < 0:
            # Window is partially or fully to the left of primary monitor
            logger.warning(f"Window has negative x position: {window_x}")
            return False

        logger.debug(f"Window is on primary monitor: x={window_x}")
        return True

    except AttributeError as e:
        logger.error(f"Window object missing 'left' attribute: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking monitor position: {e}")
        return False


def get_screen_resolution() -> Tuple[int, int]:
    """Get the current screen resolution.

    Returns:
        Tuple of (width, height) in pixels
    """
    try:
        width, height = pyautogui.size()
        logger.debug(f"Screen resolution: {width}x{height}")
        return (width, height)
    except Exception as e:
        logger.error(f"Error getting screen resolution: {e}")
        return (0, 0)


def validate_startup(settings: dict) -> Tuple[bool, str]:
    """Perform all startup validation checks.

    Checks:
    1. TaxAct window is found
    2. TaxAct is on primary monitor
    3. Screen resolution matches expected (warning only)

    Args:
        settings: Settings dict with display configuration

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check for skip validation (dev mode without local TaxAct)
    if settings.get("skip_taxact_validation", False):
        logger.warning("TaxAct validation SKIPPED (skip_taxact_validation=true)")
        return (True, "TaxAct validation skipped (dev mode)")

    display_settings = settings.get("display", {})
    window_title = display_settings.get("taxact_window_title", "TaxAct")
    expected_width = display_settings.get("expected_width", 1920)
    expected_height = display_settings.get("expected_height", 1080)
    require_primary = display_settings.get("require_primary_monitor", True)

    # Check 1: Find TaxAct window
    logger.info("Validating startup...")
    window = find_taxact_window(window_title)

    if window is None:
        msg = f"TaxAct window not found. Please open TaxAct and ensure '{window_title}' is in the window title."
        logger.error(msg)
        return (False, msg)

    # Check 2: Verify window is on primary monitor
    if require_primary:
        if not is_on_primary_monitor(window, max_x=expected_width):
            msg = f"TaxAct is not on the primary monitor. Please move TaxAct to the primary monitor (x < {expected_width})."
            logger.error(msg)
            return (False, msg)

    # Check 3: Verify screen resolution (warning only)
    width, height = get_screen_resolution()

    if width != expected_width or height != expected_height:
        logger.warning(
            f"Screen resolution mismatch: {width}x{height} (expected {expected_width}x{expected_height}). "
            "Coordinates may not work correctly."
        )

    # All checks passed
    msg = f"Startup validation passed. TaxAct found at ({window.left}, {window.top}), resolution {width}x{height}"
    logger.info(msg)
    return (True, msg)
