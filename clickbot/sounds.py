"""Audio feedback module using Windows winsound.

Provides audible feedback for bot operations:
- play_success(): Short beep for successful actions
- play_error(): Triple alarm for errors
- play_complete(): Ascending melody when all clients processed
- play_iteration(): Windows system sound for new iteration
"""

import logging
import time
from typing import List, Optional

logger = logging.getLogger(__name__)

# Try to import winsound (Windows only)
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False
    logger.warning("winsound not available - sound feedback disabled")


# Module-level flag to enable/disable sounds
_sounds_enabled = True


def set_enabled(enabled: bool) -> None:
    """Enable or disable all sound output.

    Args:
        enabled: True to enable sounds, False to disable
    """
    global _sounds_enabled
    _sounds_enabled = enabled
    logger.debug(f"Sounds {'enabled' if enabled else 'disabled'}")


def is_enabled() -> bool:
    """Check if sounds are currently enabled.

    Returns:
        True if sounds are enabled, False otherwise
    """
    return _sounds_enabled and WINSOUND_AVAILABLE


def play_success(freq: int = 1000, duration: int = 200) -> None:
    """Play a short success beep.

    Args:
        freq: Frequency in Hz (37-32767). Default 1000 Hz.
        duration: Duration in milliseconds. Default 200ms.
    """
    if not is_enabled():
        logger.debug("Sound disabled, skipping play_success")
        return

    try:
        # Clamp frequency to valid range
        freq = max(37, min(32767, freq))
        winsound.Beep(freq, duration)
        logger.debug(f"Played success sound: {freq}Hz for {duration}ms")
    except RuntimeError as e:
        logger.warning(f"Could not play success sound: {e}")
    except Exception as e:
        logger.error(f"Unexpected error playing success sound: {e}")


def play_error(freq: int = 400, duration: int = 500, repeats: int = 3) -> None:
    """Play an error alarm (multiple beeps).

    Args:
        freq: Frequency in Hz (37-32767). Default 400 Hz (low tone).
        duration: Duration per beep in milliseconds. Default 500ms.
        repeats: Number of beeps. Default 3.
    """
    if not is_enabled():
        logger.debug("Sound disabled, skipping play_error")
        return

    try:
        # Clamp frequency to valid range
        freq = max(37, min(32767, freq))

        for i in range(repeats):
            winsound.Beep(freq, duration)
            if i < repeats - 1:
                time.sleep(0.1)  # Short pause between beeps

        logger.debug(f"Played error sound: {freq}Hz x {repeats}")
    except RuntimeError as e:
        logger.warning(f"Could not play error sound: {e}")
    except Exception as e:
        logger.error(f"Unexpected error playing error sound: {e}")


def play_complete(frequencies: Optional[List[int]] = None) -> None:
    """Play an ascending melody to indicate completion.

    Args:
        frequencies: List of frequencies to play in sequence.
                    Default is [523, 659, 784] (C5, E5, G5 - C major chord).
    """
    if not is_enabled():
        logger.debug("Sound disabled, skipping play_complete")
        return

    if frequencies is None:
        frequencies = [523, 659, 784]  # C5, E5, G5

    try:
        for freq in frequencies:
            # Clamp frequency to valid range
            freq = max(37, min(32767, freq))
            winsound.Beep(freq, 200)
            time.sleep(0.05)  # Small gap between notes

        logger.debug(f"Played complete melody: {frequencies}")
    except RuntimeError as e:
        logger.warning(f"Could not play complete sound: {e}")
    except Exception as e:
        logger.error(f"Unexpected error playing complete sound: {e}")


def play_click(freq: int = 1200, duration: int = 120) -> None:
    """Play a clear tick sound when a click is executed.

    Args:
        freq: Frequency in Hz. Default 1200 Hz.
        duration: Duration in milliseconds. Default 120ms.
    """
    if not is_enabled():
        return

    try:
        freq = max(37, min(32767, freq))
        winsound.Beep(freq, duration)
    except Exception:
        pass  # Never block execution for a click sound


def play_iteration() -> None:
    """Play Windows system sound for new iteration.

    Uses the Windows "SystemAsterisk" sound which is a familiar,
    non-intrusive notification sound.
    """
    if not is_enabled():
        logger.debug("Sound disabled, skipping play_iteration")
        return

    try:
        # SND_ALIAS: Play system sound by name
        # SND_ASYNC: Play asynchronously (don't block)
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        logger.debug("Played iteration sound: SystemAsterisk")
    except Exception as e:
        logger.warning(f"Could not play iteration sound: {e}")
