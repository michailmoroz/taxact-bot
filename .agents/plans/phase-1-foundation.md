# Feature: Phase 1 - Foundation

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

## Feature Description

Phase 1 establishes the core infrastructure for the TaxAct Form 7004 Automation Bot. This includes the project structure, configuration files, and foundational modules (executor, sounds, window_validator). At the end of this phase, the bot can:
- Detect if TaxAct is open and on the primary monitor
- Execute basic click/type/scroll actions
- Provide audio feedback (success, error, complete sounds)
- Respond to hotkeys (F6 start, F7 stop, F8 pause)

## User Story

As a **tax preparer** I want to **start the bot with a hotkey and have it validate the TaxAct window position** so that **I can be confident the automation will work correctly before it starts clicking**.

## Problem Statement

Manual Form 7004 E-Filing requires ~20+ repetitive clicks per client. Before automating this process, we need a solid foundation: window detection, basic actions, audio feedback, and hotkey control.

## Solution Statement

Create a modular Python project with:
1. **executor.py** - Low-level PyAutoGUI wrapper for click/type/scroll
2. **sounds.py** - Windows audio feedback using winsound
3. **window_validator.py** - TaxAct window detection with multi-monitor support
4. **main.py** - Entry point with hotkey registration and orchestration

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: Medium
**Primary Systems Affected**: All (new project)
**Dependencies**: PyAutoGUI, keyboard, PyGetWindow, winsound (built-in)

---

## CONTEXT REFERENCES

### Relevant Codebase Files (MUST READ BEFORE IMPLEMENTING!)

| File | Lines | Why |
|------|-------|-----|
| `.agents/PRD.md` | 452-620 | API specifications for all modules |
| `.agents/PRD.md` | 506-537 | settings.json schema |
| `CLAUDE.md` | 1-100 | Coding standards, error handling patterns |
| `CLAUDE.md` | 100-180 | Logging standards |

### New Files to Create

| File | Purpose |
|------|---------|
| `clickbot/__init__.py` | Package marker |
| `clickbot/main.py` | Entry point, hotkey handling, orchestration |
| `clickbot/executor.py` | PyAutoGUI wrapper (click, type, scroll, wait) |
| `clickbot/sounds.py` | Audio feedback (success, error, complete) |
| `clickbot/window_validator.py` | TaxAct detection, monitor validation |
| `config/settings.json` | Global configuration |
| `requirements.txt` | Python dependencies |

### Relevant Documentation

| Source | Section | Why |
|--------|---------|-----|
| [PyAutoGUI Quickstart](https://pyautogui.readthedocs.io/en/latest/quickstart.html) | Full page | Click, type, scroll API |
| [PyAutoGUI Mouse Functions](https://pyautogui.readthedocs.io/en/latest/mouse.html) | Click, doubleClick | Mouse automation |
| [winsound Docs](https://docs.python.org/3/library/winsound.html) | Beep() | Audio feedback |
| [keyboard PyPI](https://pypi.org/project/keyboard/) | add_hotkey | Global hotkey registration |
| [PyGetWindow Docs](https://pygetwindow.readthedocs.io/) | getWindowsWithTitle | Window detection |

### Patterns to Follow

**Naming Conventions (from CLAUDE.md):**
```python
# Modules: lowercase_with_underscores
window_validator.py

# Functions: lowercase_with_underscores
def find_taxact_window():

# Constants: UPPERCASE_WITH_UNDERSCORES
DEFAULT_WAIT_SECONDS = 2.0
```

**Error Handling (from CLAUDE.md):**
```python
import logging

logger = logging.getLogger(__name__)

def execute_step(step):
    try:
        logger.info(f"Executing: {step.name}")
        result = _perform_action(step)
        return result
    except Exception as e:
        logger.error(f"Failed: {e}")
        sounds.play_error()
        raise
```

**Type Hints (from CLAUDE.md):**
```python
from typing import Optional, Tuple

def click(x: int, y: int, wait: float = 2.0) -> bool:
    """Execute a click at the specified coordinates."""
    ...
```

**Logging Pattern:**
```python
import logging
logger = logging.getLogger(__name__)

# DEBUG: Detailed diagnostic (coordinates, timing)
# INFO: Normal operation ("Starting bot", "Click at (500, 300)")
# WARNING: Recoverable issues ("OCR confidence low")
# ERROR: Operation failed ("TaxAct window not found")
# CRITICAL: Bot cannot continue ("Fail-safe triggered")
```

---

## IMPLEMENTATION PLAN

### Phase 1.1: Project Structure & Dependencies

Create the basic project structure with all necessary directories and the requirements.txt file.

**Tasks:**
- Create clickbot/ package directory
- Create config/ directory
- Create requirements.txt with pinned versions
- Create empty __init__.py

### Phase 1.2: Configuration

Create settings.json with all configuration options as specified in PRD.

**Tasks:**
- Create config/settings.json with full schema
- Include dev_mode, hotkeys, timing, sounds, OCR, display settings

### Phase 1.3: Sounds Module

Implement audio feedback using winsound. This module has no dependencies on other modules.

**Tasks:**
- Implement play_success() - short confirmation beep
- Implement play_error() - triple alarm tone
- Implement play_complete() - ascending melody
- Add enable/disable via settings

### Phase 1.4: Executor Module

Implement PyAutoGUI wrapper with safety features and logging.

**Tasks:**
- Implement click(x, y, wait) with fail-safe
- Implement double_click(x, y, wait)
- Implement type_text(text, interval)
- Implement scroll(clicks, x, y)
- Implement wait(seconds)
- Add coordinate validation
- Add dev_mode support (slower actions for visibility)

### Phase 1.5: Window Validator Module

Implement TaxAct window detection and monitor validation.

**Tasks:**
- Implement find_taxact_window() using PyGetWindow
- Implement is_on_primary_monitor(window) - check x < 1920
- Implement get_screen_resolution()
- Implement validate_startup() - orchestrates all checks

### Phase 1.6: Main Entry Point

Implement main.py with hotkey registration and basic orchestration.

**Tasks:**
- Load settings from config/settings.json
- Register hotkeys (F6 start, F7 stop, F8 pause)
- Implement start/stop/pause state machine
- Call validate_startup() before any automation
- Set up logging

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

---

### Task 1: CREATE requirements.txt

- **IMPLEMENT**: Pin all dependencies with minimum versions
- **CONTENT**:
  ```
  pyautogui>=0.9.54
  keyboard>=0.13.5
  PyGetWindow>=0.0.9
  Pillow>=10.0.0
  ```
- **VALIDATE**: `pip install -r requirements.txt`

---

### Task 2: CREATE clickbot/__init__.py

- **IMPLEMENT**: Empty package marker with version
- **CONTENT**:
  ```python
  """TaxAct Form 7004 Automation Bot."""
  __version__ = "0.1.0"
  ```
- **VALIDATE**: `python -c "import clickbot; print(clickbot.__version__)"`

---

### Task 3: CREATE config/settings.json

- **IMPLEMENT**: Full configuration schema from PRD Section 9
- **PATTERN**: PRD.md:506-537
- **CONTENT**:
  ```json
  {
    "dev_mode": true,
    "hotkeys": {
      "start": "F6",
      "stop": "F7",
      "pause": "F8"
    },
    "timing": {
      "default_wait": 2.0,
      "long_wait": 5.0,
      "scroll_wait": 0.5,
      "typing_interval": 0.05
    },
    "sounds": {
      "enabled": true,
      "success_freq": 1000,
      "success_duration": 200,
      "error_freq": 400,
      "error_duration": 500,
      "complete_frequencies": [523, 659, 784]
    },
    "ocr": {
      "tesseract_path": "C:/Program Files/Tesseract-OCR/tesseract.exe",
      "language": "eng"
    },
    "display": {
      "expected_width": 1920,
      "expected_height": 1080,
      "require_primary_monitor": true,
      "taxact_window_title": "TaxAct"
    }
  }
  ```
- **VALIDATE**: `python -c "import json; json.load(open('config/settings.json'))"`

---

### Task 4: CREATE clickbot/sounds.py

- **IMPLEMENT**: Audio feedback module using winsound
- **IMPORTS**: `import winsound`, `import logging`, `from typing import List`
- **PATTERN**: Error handling from CLAUDE.md
- **FUNCTIONS**:
  - `play_success(freq: int = 1000, duration: int = 200) -> None`
  - `play_error(freq: int = 400, duration: int = 500, repeats: int = 3) -> None`
  - `play_complete(frequencies: List[int] = None) -> None`
- **GOTCHA**: winsound.Beep frequency must be 37-32767 Hz
- **GOTCHA**: winsound only works on Windows (not in VMs/Remote Desktop)
- **VALIDATE**: `python -c "from clickbot.sounds import play_success; play_success()"`

---

### Task 5: CREATE clickbot/executor.py

- **IMPLEMENT**: PyAutoGUI wrapper with safety and logging
- **IMPORTS**: `import pyautogui`, `import logging`, `import time`, `from typing import Optional, Tuple`
- **PATTERN**: Type hints and error handling from CLAUDE.md
- **FUNCTIONS**:
  - `click(x: int, y: int, wait: float = 2.0) -> bool`
  - `double_click(x: int, y: int, wait: float = 5.0) -> bool`
  - `type_text(text: str, interval: float = 0.05) -> bool`
  - `scroll(clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> bool`
  - `wait(seconds: float) -> None`
- **SAFETY**:
  - Set `pyautogui.FAILSAFE = True` (mouse to corner aborts)
  - Set `pyautogui.PAUSE = 0.1` (small pause between actions)
  - Validate coordinates are within screen bounds
- **GOTCHA**: pyautogui.click() blocks until complete
- **GOTCHA**: scroll() positive = up, negative = down
- **VALIDATE**: `python -c "from clickbot.executor import click; print('executor loaded')"`

---

### Task 6: CREATE clickbot/window_validator.py

- **IMPLEMENT**: TaxAct window detection with multi-monitor support
- **IMPORTS**: `import pygetwindow as gw`, `import pyautogui`, `import logging`, `from typing import Optional, Tuple`
- **PATTERN**: Type hints from CLAUDE.md
- **FUNCTIONS**:
  - `find_taxact_window(title: str = "TaxAct") -> Optional[object]`
  - `is_on_primary_monitor(window, max_x: int = 1920) -> bool`
  - `get_screen_resolution() -> Tuple[int, int]`
  - `validate_startup(settings: dict) -> Tuple[bool, str]`
- **LOGIC for validate_startup**:
  1. Call find_taxact_window() - if None, return (False, "TaxAct not found")
  2. Call is_on_primary_monitor() - if False, return (False, "TaxAct not on primary monitor")
  3. Call get_screen_resolution() - warn if not 1920x1080
  4. Return (True, "OK")
- **GOTCHA**: PyGetWindow returns list, need [0] or handle empty
- **GOTCHA**: Window.left gives x position (< 1920 = primary monitor)
- **VALIDATE**: `python -c "from clickbot.window_validator import get_screen_resolution; print(get_screen_resolution())"`

---

### Task 7: CREATE clickbot/main.py

- **IMPLEMENT**: Entry point with hotkeys and orchestration
- **IMPORTS**: `import keyboard`, `import json`, `import logging`, `import time`, `from pathlib import Path`
- **IMPORTS LOCAL**: `from clickbot import sounds`, `from clickbot import executor`, `from clickbot import window_validator`
- **PATTERN**: Logging setup from CLAUDE.md
- **FUNCTIONS**:
  - `load_settings(path: Path) -> dict`
  - `setup_logging(dev_mode: bool) -> None`
  - `on_start() -> None` - validates and starts bot
  - `on_stop() -> None` - immediate stop
  - `on_pause() -> None` - toggle pause
  - `main() -> None` - entry point
- **STATE MACHINE**:
  ```python
  class BotState:
      IDLE = "idle"
      RUNNING = "running"
      PAUSED = "paused"

  current_state = BotState.IDLE
  ```
- **HOTKEY REGISTRATION**:
  ```python
  keyboard.add_hotkey(settings["hotkeys"]["start"], on_start)
  keyboard.add_hotkey(settings["hotkeys"]["stop"], on_stop)
  keyboard.add_hotkey(settings["hotkeys"]["pause"], on_pause)
  ```
- **GOTCHA**: keyboard works WITHOUT admin on Windows for normal apps (TaxAct). Admin only needed for Task Manager, UAC dialogs, or games with anti-cheat. On Linux, root/sudo is always required.
- **GOTCHA**: Use keyboard.wait() to keep script alive
- **VALIDATE**: `python -m clickbot.main` (should print "Bot ready. Press F6 to start.")

---

### Task 8: ADD manual test for Phase 1

- **IMPLEMENT**: Simple integration test script
- **CREATE**: `tests/manual/test_phase1.py`
- **CONTENT**: Script that:
  1. Imports all modules
  2. Plays success sound
  3. Prints screen resolution
  4. Checks for TaxAct window
  5. Clicks at (100, 100) if confirmed
- **VALIDATE**: `python tests/manual/test_phase1.py`

---

## TESTING STRATEGY

### Unit Tests (Phase 1 - Manual)

For Phase 1, testing is primarily manual due to hardware dependencies (screen, sound, windows).

**sounds.py:**
- Verify play_success() produces audible beep
- Verify play_error() produces 3 beeps
- Verify play_complete() produces ascending melody

**executor.py:**
- Verify click() moves mouse to position
- Verify type_text() types characters
- Verify scroll() scrolls the page
- Verify fail-safe triggers when mouse in corner

**window_validator.py:**
- Verify find_taxact_window() finds TaxAct when open
- Verify find_taxact_window() returns None when TaxAct closed
- Verify is_on_primary_monitor() correctly checks x < 1920

### Integration Tests

**main.py:**
- F6 should trigger on_start()
- F7 should trigger on_stop()
- F8 should toggle pause state
- validate_startup() should be called before any action

### Edge Cases

- TaxAct window not open → play_error() + message
- TaxAct on secondary monitor (x >= 1920) → play_error() + message
- Invalid coordinates (negative, off-screen) → log warning, don't crash
- winsound fails (VM/Remote Desktop) → catch exception, continue

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
# Check syntax
python -m py_compile clickbot/sounds.py
python -m py_compile clickbot/executor.py
python -m py_compile clickbot/window_validator.py
python -m py_compile clickbot/main.py

# Lint (if ruff installed)
ruff check clickbot/
```

### Level 2: Import Tests

```bash
python -c "from clickbot.sounds import play_success, play_error, play_complete"
python -c "from clickbot.executor import click, double_click, type_text, scroll, wait"
python -c "from clickbot.window_validator import find_taxact_window, validate_startup"
python -c "from clickbot.main import load_settings, main"
```

### Level 3: Functional Tests

```bash
# Test sounds (will produce audio)
python -c "from clickbot.sounds import play_success; play_success()"

# Test screen resolution
python -c "from clickbot.window_validator import get_screen_resolution; print(get_screen_resolution())"

# Test settings loading
python -c "from clickbot.main import load_settings; from pathlib import Path; print(load_settings(Path('config/settings.json')))"
```

### Level 4: Manual Validation

1. Open TaxAct 2025 Professional on primary monitor
2. Run `python -m clickbot.main`
3. Verify "Bot ready" message appears
4. Press F6 → should validate TaxAct and print success
5. Press F7 → should stop (if running)
6. Press F8 → should toggle pause
7. Close TaxAct, press F6 → should play error sound

---

## ACCEPTANCE CRITERIA

- [x] Project structure created (clickbot/, config/, requirements.txt)
- [ ] All dependencies install without error
- [ ] settings.json loads and parses correctly
- [ ] sounds.py produces audible feedback (success, error, complete)
- [ ] executor.py executes click/type/scroll actions
- [ ] window_validator.py detects TaxAct window
- [ ] window_validator.py validates primary monitor position (x < 1920)
- [ ] main.py responds to F6/F7/F8 hotkeys
- [ ] main.py calls validate_startup() before any automation
- [ ] Error sound plays when TaxAct not found or on wrong monitor
- [ ] All validation commands pass

---

## COMPLETION CHECKLIST

- [ ] Task 1: requirements.txt created and tested
- [ ] Task 2: clickbot/__init__.py created
- [ ] Task 3: config/settings.json created and valid JSON
- [ ] Task 4: sounds.py implemented with all 3 functions
- [ ] Task 5: executor.py implemented with safety features
- [ ] Task 6: window_validator.py implemented with monitor check
- [ ] Task 7: main.py implemented with hotkeys
- [ ] Task 8: Manual test script created
- [ ] All Level 1-4 validation commands pass
- [ ] Manual testing confirms hotkeys work
- [ ] Manual testing confirms TaxAct detection works

---

## NOTES

### Design Decisions

1. **PyGetWindow vs PyWinCtl**: Using PyGetWindow for simplicity. PyWinCtl offers better multi-monitor support but adds complexity. PyGetWindow's `.left` property is sufficient to check if window is on primary monitor (x < 1920).

2. **Singleton vs Module-Level State**: Using module-level state in main.py (`current_state`) rather than Singleton pattern for simplicity. Can refactor to class-based approach in Phase 4 if needed.

3. **No Settings Class**: Loading settings as dict rather than dataclass for Phase 1. Can add typed Settings class in future phases for better IDE support.

4. **Manual Tests Only**: Deferring pytest setup to Phase 4. Hardware-dependent code (clicks, sounds, windows) is difficult to unit test meaningfully.

### Known Limitations

- **Windows Only**: winsound and PyGetWindow are Windows-specific
- **Admin NOT Required**: keyboard library works without admin on Windows for normal desktop apps like TaxAct. Admin is only needed for: Task Manager, UAC dialogs, games with anti-cheat, or keystroke recording. (Verified via [keyboard PyPI](https://pypi.org/project/keyboard/) and [StackAbuse Guide](https://stackabuse.com/guide-to-pythons-keyboard-module/))
- **Resolution Hardcoded**: Assumes 1920x1080, coordinates will be wrong on other resolutions
- **No OCR Yet**: OCR (pytesseract) deferred to Phase 3

### Risk Mitigations

- **Fail-Safe Enabled**: Mouse to upper-left corner aborts all PyAutoGUI actions
- **Validation First**: Always call validate_startup() before any automation
- **Audio Feedback**: User always knows when something goes wrong

---

## Sources (Research References)

- [PyAutoGUI Quickstart](https://pyautogui.readthedocs.io/en/latest/quickstart.html)
- [PyAutoGUI Mouse Functions](https://pyautogui.readthedocs.io/en/latest/mouse.html)
- [Python winsound Documentation](https://docs.python.org/3/library/winsound.html)
- [keyboard PyPI](https://pypi.org/project/keyboard/)
- [keyboard GitHub - Admin Rights Discussion](https://github.com/boppreh/keyboard)
- [Guide to Python's keyboard Module - StackAbuse](https://stackabuse.com/guide-to-pythons-keyboard-module/)
- [PyGetWindow Documentation](https://pygetwindow.readthedocs.io/)
- [Automate the Boring Stuff - Chapter 18](https://automatetheboringstuff.com/chapter18/)
