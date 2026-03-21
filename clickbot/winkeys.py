"""Low-level Windows keyboard input using atomic SendInput.

Provides send_ctrl_home() for reliably sending Ctrl+Home to applications
like TaxAct that require proper scan codes and KEYEVENTF_EXTENDEDKEY.

Why this exists:
- pyautogui uses deprecated keybd_event() with scan code=0, no extended flag
- pydirectinput only sets KEYEVENTF_EXTENDEDKEY for arrow keys, not Home
- pydirectinput sends each key as a separate SendInput() call (non-atomic)
- This module sends all key events in a SINGLE SendInput() call with
  correct scan codes and flags, guaranteed atomic per Microsoft docs.
"""

import ctypes
from ctypes import wintypes
import logging

logger = logging.getLogger(__name__)

# Constants
INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Hardware scan codes
SCAN_CTRL = 0x1D   # Left Ctrl
SCAN_HOME = 0x47   # Home (navigation cluster, needs EXTENDEDKEY)


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", _INPUT_UNION),
    ]


def _make_key(scan_code: int, flags: int) -> INPUT:
    """Create an INPUT struct for a keyboard scan code event."""
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = 0
    inp.union.ki.wScan = scan_code
    inp.union.ki.dwFlags = flags
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = None
    return inp


def send_ctrl_home() -> bool:
    """Send Ctrl+Home as a single atomic SendInput call.

    All 4 key events (Ctrl down, Home down, Home up, Ctrl up) are sent
    in one SendInput() call, so no other input can interleave.

    Returns:
        True if all 4 events were injected successfully.
    """
    inputs = (INPUT * 4)(
        _make_key(SCAN_CTRL, KEYEVENTF_SCANCODE),
        _make_key(SCAN_HOME, KEYEVENTF_SCANCODE | KEYEVENTF_EXTENDEDKEY),
        _make_key(SCAN_HOME, KEYEVENTF_SCANCODE | KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP),
        _make_key(SCAN_CTRL, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP),
    )

    result = ctypes.windll.user32.SendInput(4, inputs, ctypes.sizeof(INPUT))
    success = result == 4

    if success:
        logger.debug("Sent Ctrl+Home (atomic SendInput, 4 events)")
    else:
        logger.error(f"SendInput Ctrl+Home failed: only {result}/4 events sent")

    return success
