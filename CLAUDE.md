# CLAUDE.md - TaxAct Form 7004 Automation Bot

## Project Overview

Desktop automation bot for TaxAct 2025 Professional Edition that automates Form 7004 E-File extension submissions. The bot navigates through ~20+ clicks per client, fills form data when needed, and processes multiple clients without duplicates.

**PRD:** `.agents/PRD.md`

---

## Critical Rules

- **IMMER ALLES PUSHEN**: Wenn Dateien verändert, erstellt oder im Code referenziert werden (Templates, Screenshots, Configs, etc.), müssen sie ALLE committed und gepusht werden. Niemals nur den Code pushen und referenzierte Assets vergessen.

---

## Architecture Principles

### Module Responsibilities

| Module | Responsibility | Rules |
|--------|----------------|-------|
| `main.py` | Entry point, orchestration, hotkeys | No direct PyAutoGUI calls |
| `executor.py` | Low-level actions (click, type, scroll) | No business logic, only actions |
| `vision.py` | OCR, screen reading | No actions, only reading |
| `state.py` | Client tracking | No I/O, pure state management |
| `window_validator.py` | Window detection, monitor validation | Called only at startup |
| `sounds.py` | Audio feedback | Stateless, fire-and-forget |
| `overlay.py` | Dev mode visualization | Optional, non-blocking |
| `recorder.py` | Coordinate capture utility | Standalone tool |

### Separation of Concerns

```
Configuration (JSON) → Process Logic (main.py) → Actions (executor.py)
                                ↓
                         Vision (vision.py) → Decisions
```

### Key Rules

1. **No hardcoded coordinates** - All coordinates in `config/processes/*.json`
2. **No hardcoded waits** - All timing in `config/settings.json`
3. **No hardcoded text** - All static inputs in process config
4. **Single Responsibility** - Each module does ONE thing well
5. **Fail-Safe First** - Always provide escape routes (hotkeys, timeouts)

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Main language |
| PyAutoGUI | 0.9.54+ | Mouse/Keyboard automation |
| pytesseract | 0.3.10+ | OCR wrapper |
| Pillow | 10.0+ | Image processing |
| keyboard | 0.13.5+ | Global hotkeys |
| PyGetWindow | 0.0.9+ | Window detection |
| pytest | 8.0+ | Testing framework |
| pytest-cov | 4.0+ | Coverage reporting |

---

## Coding Standards

### Python Style

- **PEP 8** compliant (use `ruff` or `black` for formatting)
- **Type hints** on all function signatures
- **Docstrings** for all public functions (Google style)
- **Max line length:** 100 characters
- **Imports:** stdlib → third-party → local (separated by blank lines)

### Naming Conventions

```python
# Modules: lowercase_with_underscores
window_validator.py

# Classes: PascalCase
class ClientTracker:

# Functions/Methods: lowercase_with_underscores
def find_next_client():

# Constants: UPPERCASE_WITH_UNDERSCORES
DEFAULT_WAIT_SECONDS = 2.0

# Private: prefix with underscore
def _internal_helper():
```

### Type Hints

```python
from typing import Optional, Tuple, List
from dataclasses import dataclass

@dataclass
class ClickResult:
    success: bool
    position: Tuple[int, int]
    error: Optional[str] = None

def click(x: int, y: int, wait: float = 2.0) -> ClickResult:
    """Execute a click at the specified coordinates."""
    ...
```

### Error Handling Pattern

```python
import logging

logger = logging.getLogger(__name__)

def execute_step(step: ProcessStep) -> StepResult:
    """Execute a single process step with full error handling."""
    try:
        logger.info(f"Executing step: {step.name}", extra={
            "step_id": step.id,
            "action": step.action,
            "coordinates": (step.x, step.y)
        })

        result = _perform_action(step)

        logger.debug(f"Step completed successfully", extra={
            "step_id": step.id,
            "duration_ms": result.duration_ms
        })
        return result

    except PyAutoGUIException as e:
        logger.error(f"Action failed: {e}", extra={
            "step_id": step.id,
            "error_type": type(e).__name__
        })
        sounds.play_error()
        raise StepExecutionError(step, e) from e

    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        sounds.play_error()
        raise
```

---

## Logging Standards

### Configuration

```python
import logging
import logging.handlers
from pathlib import Path

def setup_logging(log_dir: Path, level: str = "DEBUG") -> None:
    """Configure structured logging with rotation."""

    log_dir.mkdir(parents=True, exist_ok=True)

    # Structured format for file
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s | %(extra_data)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Simple format for console
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )

    # Rotating file handler (10MB, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "bot.log",
        maxBytes=10_000_000,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
```

### Log Levels Usage

| Level | When to Use | Example |
|-------|-------------|---------|
| `DEBUG` | Detailed diagnostic info | Coordinates, OCR raw output, timing |
| `INFO` | Normal operation events | "Starting client: SANDMEYER INC", "Step 5 complete" |
| `WARNING` | Unexpected but recoverable | "OCR confidence low (65%)", "Retry attempt 2/3" |
| `ERROR` | Operation failed | "Click failed at (500, 300)", "TaxAct window not found" |
| `CRITICAL` | Bot cannot continue | "Fail-safe triggered", "Unrecoverable state" |

### Structured Logging

Always include context in `extra` dict:

```python
logger.info("Processing client", extra={
    "client_name": client.name,
    "client_index": idx,
    "total_clients": total,
    "iteration": loop_count
})

logger.error("OCR failed to read field", extra={
    "region": (x, y, w, h),
    "expected_content": "Officer Name",
    "raw_output": ocr_result,
    "confidence": confidence_score
})
```

---

## Testing Strategy

### Test Pyramid

```
         /\
        /  \      E2E Tests (Manual + Automated)
       /----\     - Full process runs
      /      \    - Real TaxAct interaction
     /--------\
    /          \  Integration Tests
   /            \ - Module interactions
  /--------------\- Config loading + execution
 /                \
/==================\ Unit Tests
                    - Pure functions
                    - Mocked dependencies
                    - Edge cases
```

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_executor.py
│   ├── test_vision.py
│   ├── test_state.py
│   ├── test_sounds.py
│   └── test_window_validator.py
├── integration/
│   ├── __init__.py
│   ├── test_config_loading.py
│   ├── test_process_execution.py
│   └── test_ocr_pipeline.py
├── e2e/
│   ├── __init__.py
│   ├── test_single_iteration.py
│   └── test_loop_mode.py
└── manual/
    └── MANUAL_TEST_CHECKLIST.md
```

### Unit Tests

```python
# tests/unit/test_executor.py
import pytest
from unittest.mock import patch, MagicMock
from clickbot.executor import click, ClickResult

class TestClick:
    """Unit tests for click function."""

    @patch('clickbot.executor.pyautogui')
    def test_click_success(self, mock_pyautogui: MagicMock) -> None:
        """Click returns success when pyautogui succeeds."""
        result = click(100, 200)

        assert result.success is True
        assert result.position == (100, 200)
        mock_pyautogui.click.assert_called_once_with(100, 200)

    @patch('clickbot.executor.pyautogui')
    def test_click_out_of_bounds(self, mock_pyautogui: MagicMock) -> None:
        """Click fails for negative coordinates."""
        result = click(-1, 200)

        assert result.success is False
        assert "out of bounds" in result.error.lower()

    @pytest.mark.parametrize("x,y", [
        (0, 0),
        (1919, 1079),
        (960, 540),
    ])
    @patch('clickbot.executor.pyautogui')
    def test_click_valid_coordinates(
        self, mock_pyautogui: MagicMock, x: int, y: int
    ) -> None:
        """Click accepts valid screen coordinates."""
        result = click(x, y)
        assert result.success is True
```

### Integration Tests

```python
# tests/integration/test_process_execution.py
import pytest
from pathlib import Path
from clickbot.config import load_process, load_settings
from clickbot.executor import Executor

class TestProcessExecution:
    """Integration tests for process execution."""

    @pytest.fixture
    def executor(self, tmp_path: Path) -> Executor:
        """Create executor with test config."""
        settings = load_settings(Path("config/settings.json"))
        return Executor(settings, dry_run=True)

    def test_load_and_validate_process(self) -> None:
        """Process config loads and validates correctly."""
        process = load_process(Path("config/processes/taxact_extension.json"))

        assert process.name == "TaxAct Form 7004 Extension"
        assert len(process.steps) > 0
        assert all(step.id for step in process.steps)

    def test_dry_run_single_step(self, executor: Executor) -> None:
        """Executor can dry-run a single step."""
        process = load_process(Path("config/processes/taxact_extension.json"))

        result = executor.execute_step(process.steps[0])

        assert result.success is True
        assert result.dry_run is True
```

### E2E Tests

```python
# tests/e2e/test_single_iteration.py
import pytest
from clickbot.main import Bot

@pytest.mark.e2e
@pytest.mark.manual
class TestSingleIteration:
    """
    E2E tests requiring real TaxAct instance.

    Prerequisites:
    - TaxAct 2025 open on primary monitor
    - Client Manager view visible
    - At least one client with empty Fed EF Status
    """

    @pytest.mark.skip(reason="Requires manual execution")
    def test_complete_single_client(self) -> None:
        """Bot completes one full iteration."""
        bot = Bot(config_path=Path("config/settings.json"))

        result = bot.run_single_iteration()

        assert result.success is True
        assert result.client_name is not None
        assert result.steps_completed == result.total_steps
```

### Manual Test Checklist

After each plan execution via `/execute`, run through:

```markdown
# Manual Test Checklist

## Pre-Test Setup
- [ ] TaxAct 2025 Professional open
- [ ] Client Manager view visible
- [ ] At least 3 clients with empty Fed EF Status
- [ ] Bot running in dev_mode: true
- [ ] Sound enabled

## Phase 1: Foundation
- [ ] F6 starts the bot
- [ ] F7 stops the bot immediately
- [ ] F8 pauses/resumes
- [ ] Error sound plays when TaxAct not found
- [ ] Error sound plays when TaxAct on wrong monitor

## Phase 2: Single Iteration
- [ ] Bot clicks through all screens
- [ ] Scroll works on Tax Liability screen
- [ ] Officer fields get filled when empty
- [ ] Bot returns to Client Manager

## Phase 3: OCR
- [ ] Bot identifies empty Fed EF Status
- [ ] Bot detects empty Officer fields
- [ ] OCR reads client name correctly

## Phase 4: Loop Mode
- [ ] Bot processes multiple clients
- [ ] No client processed twice
- [ ] Completion sound plays when done
```

### Running Tests

```bash
# All unit tests
pytest tests/unit -v

# With coverage
pytest tests/unit --cov=clickbot --cov-report=html

# Integration tests
pytest tests/integration -v

# Specific test file
pytest tests/unit/test_executor.py -v

# Run by marker
pytest -m "not e2e" -v
```

### Coverage Requirements

| Module | Minimum Coverage |
|--------|-----------------|
| executor.py | 90% |
| vision.py | 85% |
| state.py | 95% |
| window_validator.py | 90% |
| sounds.py | 80% |
| **Overall** | **85%** |

---

## Configuration Management

### Settings Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["dev_mode", "hotkeys", "timing", "sounds", "ocr", "display"],
  "properties": {
    "dev_mode": { "type": "boolean" },
    "hotkeys": {
      "type": "object",
      "properties": {
        "start": { "type": "string" },
        "stop": { "type": "string" },
        "pause": { "type": "string" }
      }
    }
  }
}
```

### Environment-Specific Config

```
config/
├── settings.json          # Default/development
├── settings.prod.json     # Production overrides
└── processes/
    └── taxact_extension.json
```

---

## Development Workflow

### Feature Implementation

1. **Plan:** Create plan via `/plan-feature`
2. **Review:** Check generated plan in `.agents/plans/`
3. **Execute:** Run plan via `/execute [plan-file]`
4. **Test:** Run test suite + manual checklist
5. **Verify:** Ensure coverage meets requirements

### Commit Convention

```
<type>(<scope>): <description>

Types: feat, fix, refactor, test, docs, chore
Scope: executor, vision, state, config, etc.

Examples:
feat(executor): add scroll action with configurable speed
fix(vision): improve OCR accuracy for low contrast text
test(state): add edge case tests for duplicate detection
```

### Pre-Commit Checks

```bash
# Format
ruff format .

# Lint
ruff check .

# Type check
mypy clickbot/

# Tests
pytest tests/unit -v
```

---

## Project-Specific Rules

### Automation Safety

1. **Always register fail-safe** - Mouse to corner aborts
2. **Always validate window** - Check TaxAct position before any action
3. **Always log before action** - Log coordinates before clicking
4. **Always sound on error** - User must know when something fails
5. **Never skip waits** - Timing issues cause cascading failures

### OCR Best Practices

1. **Use regions, not full screen** - Faster and more accurate
2. **Preprocess images** - Grayscale, threshold, denoise
3. **Log raw output** - Debug OCR failures
4. **Have fallback** - If OCR fails, stop safely

### Coordinate Management

1. **Always use named coordinates** - `"continue_button"` not `(500, 300)`
2. **Group by screen** - Each screen has its own coordinate set
3. **Include tolerance** - Allow small variations
4. **Document with screenshots** - Reference images in `.agents/screenshots/`

---

## File Structure

```
clickbot_1/
├── CLAUDE.md                    # This file
├── README.md                    # User documentation
├── requirements.txt             # Dependencies
├── requirements-dev.txt         # Dev dependencies (pytest, ruff, mypy)
├── pyproject.toml              # Project config
│
├── clickbot/                   # Main package
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── executor.py             # Actions
│   ├── vision.py               # OCR
│   ├── state.py                # Client tracking
│   ├── window_validator.py     # Startup validation
│   ├── sounds.py               # Audio feedback
│   ├── overlay.py              # Dev visualization
│   └── recorder.py             # Coordinate tool
│
├── config/
│   ├── settings.json
│   └── processes/
│       └── taxact_extension.json
│
├── tests/                      # Test suite
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── manual/
│
├── logs/                       # Runtime logs (gitignored)
│
└── .agents/
    ├── PRD.md                  # Requirements
    ├── plans/                  # Feature plans
    └── screenshots/            # Reference images
```

---

## Quick Reference

### Common Commands

```bash
# Run bot
python -m clickbot.main

# Run with specific config
python -m clickbot.main --config config/settings.prod.json

# Record coordinates
python -m clickbot.recorder

# Run tests
pytest tests/unit -v --cov=clickbot
```

### Hotkeys (Default)

| Key | Action |
|-----|--------|
| F6 | Start bot |
| F7 | Stop bot (immediate) |
| F8 | Pause/Resume |

### Log Locations

| Log | Path |
|-----|------|
| Main log | `logs/bot.log` |
| Error log | `logs/error.log` |
| OCR debug | `logs/ocr_debug/` |

---

*Last updated: 2026-02-04*
