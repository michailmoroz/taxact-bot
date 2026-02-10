"""Low-level automation actions using PyAutoGUI.

Provides safe wrappers around PyAutoGUI functions with:
- Fail-safe enabled (mouse to corner aborts)
- Coordinate validation
- Logging for all actions
- Dev mode support for slower execution
"""

import logging
import time
from typing import Optional, Tuple

import pyautogui

logger = logging.getLogger(__name__)

# Safety settings
pyautogui.FAILSAFE = True  # Move mouse to upper-left corner to abort
pyautogui.PAUSE = 0.1  # Small pause between PyAutoGUI actions

# Module-level dev_mode flag
_dev_mode = False


def set_dev_mode(enabled: bool) -> None:
    """Enable or disable dev mode (slower execution for visibility).

    Args:
        enabled: True to enable dev mode, False for normal speed
    """
    global _dev_mode
    _dev_mode = enabled
    logger.debug(f"Dev mode {'enabled' if enabled else 'disabled'}")


def is_dev_mode() -> bool:
    """Check if dev mode is currently enabled.

    Returns:
        True if dev mode is enabled, False otherwise
    """
    return _dev_mode


def get_screen_size() -> Tuple[int, int]:
    """Get the current screen resolution.

    Returns:
        Tuple of (width, height) in pixels
    """
    return pyautogui.size()


def _validate_coordinates(x: int, y: int) -> bool:
    """Validate that coordinates are within screen bounds.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        True if coordinates are valid, False otherwise
    """
    width, height = get_screen_size()

    if x < 0 or y < 0:
        logger.warning(f"Negative coordinates: ({x}, {y})")
        return False

    if x >= width or y >= height:
        logger.warning(f"Coordinates out of bounds: ({x}, {y}) - screen is {width}x{height}")
        return False

    return True


def click(x: int, y: int, wait: float = 2.0) -> bool:
    """Execute a single click at the specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
        wait: Seconds to wait after click. Default 2.0.

    Returns:
        True if click was executed, False if coordinates invalid
    """
    if not _validate_coordinates(x, y):
        return False

    try:
        logger.info(f"Click at ({x}, {y})")

        if _dev_mode:
            # In dev mode, move slowly so user can see
            pyautogui.moveTo(x, y, duration=0.3)
            time.sleep(0.2)

        pyautogui.click(x, y)

        if wait > 0:
            time.sleep(wait)

        logger.debug(f"Click completed, waited {wait}s")
        return True

    except pyautogui.FailSafeException:
        logger.critical("Fail-safe triggered! Mouse moved to corner.")
        raise
    except Exception as e:
        logger.error(f"Click failed at ({x}, {y}): {e}")
        return False


def double_click(x: int, y: int, wait: float = 5.0) -> bool:
    """Execute a double click at the specified coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
        wait: Seconds to wait after double click. Default 5.0.

    Returns:
        True if double click was executed, False if coordinates invalid
    """
    if not _validate_coordinates(x, y):
        return False

    try:
        logger.info(f"Double-click at ({x}, {y})")

        if _dev_mode:
            pyautogui.moveTo(x, y, duration=0.3)
            time.sleep(0.2)

        pyautogui.doubleClick(x, y)

        if wait > 0:
            time.sleep(wait)

        logger.debug(f"Double-click completed, waited {wait}s")
        return True

    except pyautogui.FailSafeException:
        logger.critical("Fail-safe triggered! Mouse moved to corner.")
        raise
    except Exception as e:
        logger.error(f"Double-click failed at ({x}, {y}): {e}")
        return False


def type_text(text: str, interval: float = 0.05) -> bool:
    """Type text using the keyboard.

    Args:
        text: The text to type
        interval: Seconds between each keystroke. Default 0.05.

    Returns:
        True if text was typed successfully, False otherwise
    """
    if not text:
        logger.warning("Empty text provided to type_text")
        return False

    try:
        logger.info(f"Typing text: '{text[:20]}{'...' if len(text) > 20 else ''}'")

        if _dev_mode:
            # Slower typing in dev mode
            interval = max(interval, 0.1)

        pyautogui.typewrite(text, interval=interval)

        logger.debug(f"Typed {len(text)} characters")
        return True

    except pyautogui.FailSafeException:
        logger.critical("Fail-safe triggered! Mouse moved to corner.")
        raise
    except Exception as e:
        logger.error(f"Type text failed: {e}")
        return False


def scroll(clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> bool:
    """Scroll the mouse wheel.

    Args:
        clicks: Number of scroll clicks. Positive = up, negative = down.
        x: Optional X coordinate to scroll at. Uses current position if None.
        y: Optional Y coordinate to scroll at. Uses current position if None.

    Returns:
        True if scroll was executed, False otherwise
    """
    try:
        # Move to position if specified
        if x is not None and y is not None:
            if not _validate_coordinates(x, y):
                return False
            logger.info(f"Scroll {clicks} clicks at ({x}, {y})")
            pyautogui.moveTo(x, y)
        else:
            logger.info(f"Scroll {clicks} clicks at current position")

        if _dev_mode:
            time.sleep(0.2)

        pyautogui.scroll(clicks)

        logger.debug(f"Scroll completed: {clicks} clicks")
        return True

    except pyautogui.FailSafeException:
        logger.critical("Fail-safe triggered! Mouse moved to corner.")
        raise
    except Exception as e:
        logger.error(f"Scroll failed: {e}")
        return False


def wait(seconds: float) -> None:
    """Wait for the specified number of seconds.

    Args:
        seconds: Number of seconds to wait
    """
    if seconds <= 0:
        return

    logger.debug(f"Waiting {seconds}s")
    time.sleep(seconds)
