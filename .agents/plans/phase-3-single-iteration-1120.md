# Feature: Phase 3 - Single Iteration (Form 1120)

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

## Feature Description

Implementierung der ersten vollständigen Automatisierungs-Iteration für Form 1120 E-File Extension. Der Bot navigiert durch ~30 Screens, klickt Buttons, scrollt bei Bedarf, füllt Officer-Felder aus und kehrt zur Client-Manager Base zurück.

**Kern-Features:**
- **Hybrid Detection**: OpenCV Template Matching mit Koordinaten-Fallback
- **Scroll-until-visible**: Scrollt bis Button sichtbar wird
- **Checkbox-Erkennung**: Prüft ob Checkboxen ausgewählt sind
- **Textfeld-Prüfung**: Erkennt leere Felder via OCR
- **Bedingte Logik**: Reagiert auf "Error/Omission" vs "Passed Alerts"
- **Guardrails**: Stoppt bei unerwarteten Screens

## User Story

As a **Steuerberater/Tax Preparer** I want to **einen vollständigen E-File Extension Prozess für einen 1120-Client automatisch durchlaufen lassen** so that **ich Zeit spare und repetitive Klickarbeit vermeiden kann**.

## Problem Statement

Die GUI ist fertig (Phase 2), aber der Bot führt nur eine Simulation aus. Die eigentliche Automatisierungslogik mit Klicks, Scrolls und OCR-basierter Feldprüfung fehlt noch.

## Solution Statement

Implementierung von:
1. **vision.py** — Hybrid Detection (OpenCV + Fallback), OCR, Checkbox/Field-Erkennung
2. **process_loader.py** — Lädt und validiert Process-JSON
3. **process_executor.py** — Führt Steps aus mit Guardrails
4. **config/processes/1120.json** — Vollständige Step-Definition
5. **assets/buttons/** — Button-Screenshots für Template Matching
6. **Integration in bot_controller.py** — Ersetzt Simulation mit echter Automation

## Feature Metadata

**Feature Type**: New Capability
**Estimated Complexity**: High
**Primary Systems Affected**: `clickbot/vision.py`, `clickbot/process_loader.py`, `clickbot/process_executor.py`, `clickbot/bot_controller.py`, `config/processes/`
**Dependencies**: OpenCV (`opencv-python>=4.8.0`), NumPy (`numpy>=1.24.0`), pytesseract (bereits in settings)

## Key Design Decision: 100% Screenshot-basiert

**KEINE festen Koordinaten notwendig!** Alles wird via Template Matching erkannt:

| Element | Erkennungsmethode |
|---------|-------------------|
| **Buttons** | Button-Screenshot → Template Match → Klick auf Match-Position |
| **Checkboxen** | Checkbox+Label Screenshot (checked/unchecked Varianten) → Match → Klick wenn checked |
| **Textfelder** | Label-Screenshot → Match → Offset zum Feld → OCR/Klick |
| **Scroll** | Bildschirmmitte (960, 540) + scroll_until_visible für Continue-Button |

Koordinaten sind nur noch optionaler Fallback, nicht mehr notwendig.

---

## CONTEXT REFERENCES

### Relevant Codebase Files (MUST READ BEFORE IMPLEMENTING!)

| File | Lines | Why |
|------|-------|-----|
| `clickbot/executor.py` | Full | Pattern für click(), scroll(), type_text() — diese Funktionen werden von process_executor.py aufgerufen |
| `clickbot/executor.py` | 78-114 | click() Funktion mit Validierung und Error Handling |
| `clickbot/executor.py` | 187-222 | scroll() Funktion mit optionalen Koordinaten |
| `clickbot/bot_controller.py` | 121-148 | `_run()` Methode — hier wird process_executor integriert |
| `clickbot/bot_controller.py` | 29-34 | StatusMessage Dataclass für GUI-Updates |
| `clickbot/sounds.py` | Full | play_error(), play_success() für Feedback |
| `clickbot/window_validator.py` | 18-41 | find_taxact_window() Pattern für Window-Suche |
| `config/settings.json` | Full | Bestehende Settings-Struktur (timing, ocr) |
| `CLAUDE.md` | 59-141 | Coding Standards, Type Hints, Error Handling |
| `.agents/PRD.md` | 409-458 | Hybrid Detection Flow Beschreibung |
| `.agents/plans/phase-2-gui-application.md` | 1094-1249 | bot_controller.py vollständige Implementation |

### New Files to Create

| File | Purpose |
|------|---------|
| `clickbot/vision.py` | Hybrid Detection, OCR, Checkbox/Field-Erkennung |
| `clickbot/process_loader.py` | Lädt Process-JSON, validiert Schema |
| `clickbot/process_executor.py` | Führt Steps aus, Guardrails, Error Handling |
| `config/processes/1120.json` | Form 1120 Process Definition |
| `assets/buttons/common/` | Shared Button-Screenshots |
| `assets/buttons/1120/` | 1120-spezifische Button-Screenshots |

### Files to Modify

| File | Changes |
|------|---------|
| `requirements.txt` | `opencv-python>=4.8.0`, `numpy>=1.24.0` hinzufügen |
| `config/settings.json` | `vision` Section hinzufügen |
| `clickbot/bot_controller.py` | `_run()` mit ProcessExecutor ersetzen |
| `clickbot/__init__.py` | Version auf 0.3.0 erhöhen |

### Relevant Documentation

| Source | Section | Why |
|--------|---------|-----|
| [OpenCV Template Matching](https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html) | Full | cv2.matchTemplate() Verwendung |
| [PyImageSearch Multi-Scale](https://pyimagesearch.com/2015/01/26/multi-scale-template-matching-using-python-opencv/) | Full | Multi-Scale Matching für Robustheit |
| [pytesseract Docs](https://github.com/madmaze/pytesseract) | image_to_string | OCR für Textfeld-Prüfung |
| [PyAutoGUI Docs](https://pyautogui.readthedocs.io/en/latest/mouse.html) | scroll() | Scroll-Funktion Parameter |

### Patterns to Follow

**Error Handling Pattern (aus executor.py:78-114):**
```python
def some_action(x: int, y: int) -> bool:
    """Execute action with validation."""
    if not _validate_input(x, y):
        return False

    try:
        logger.info(f"Action at ({x}, {y})")
        # ... action
        return True
    except SpecificException as e:
        logger.error(f"Action failed: {e}")
        return False
```

**Logging Pattern (aus allen Modulen):**
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Starting operation")
logger.debug(f"Details: {value}")
logger.warning("Recoverable issue")
logger.error(f"Operation failed: {error}")
```

**Type Hints Pattern (aus executor.py):**
```python
from typing import Optional, Tuple, List

def function(param: str, optional: Optional[int] = None) -> Tuple[bool, str]:
    """Docstring with Args and Returns."""
    pass
```

**Message Queue Pattern (aus bot_controller.py:29-34):**
```python
@dataclass
class StatusMessage:
    type: str  # "status", "log", "error", "complete"
    message: str
    data: Optional[dict] = None

# Usage in worker thread:
self.message_queue.put(StatusMessage("log", "Step completed"))
```

**Settings Loading Pattern (aus executor.py, sounds.py):**
```python
# Module-level flag
_some_setting = False

def configure(settings: dict) -> None:
    """Configure module from settings."""
    global _some_setting
    _some_setting = settings.get("section", {}).get("key", default)
```

---

## IMPLEMENTATION PLAN

### Phase 1: Dependencies & Configuration

Installiere OpenCV/NumPy und erweitere Settings um Vision-Konfiguration.

**Tasks:**
- OpenCV und NumPy zu requirements.txt hinzufügen
- Vision-Settings in settings.json hinzufügen
- Assets-Verzeichnisstruktur erstellen
- Version in __init__.py erhöhen

### Phase 2: Vision Module (Hybrid Detection)

Erstelle vision.py mit Template Matching, OCR und Helper-Funktionen.

**Tasks:**
- Screenshot-Funktion
- Template Matching mit Confidence Threshold
- Fallback auf Koordinaten wenn nicht gefunden
- OCR für Textfelder
- Checkbox-State-Erkennung
- Scroll-until-visible Pattern

### Phase 3: Process Loader

Erstelle process_loader.py zum Laden und Validieren von Process-JSONs.

**Tasks:**
- JSON-Loading mit Error Handling
- Schema-Validierung
- Step-Iteration
- Statische Inputs (Officer-Daten)

### Phase 4: Process Executor

Erstelle process_executor.py der Steps ausführt mit Guardrails.

**Tasks:**
- Step-Ausführung (click, type, scroll, conditional)
- Guardrail-Checks (Screen-Verification)
- Error Handling mit Sound-Feedback
- Status-Updates via Message Queue

### Phase 5: Process Definition (1120.json)

Erstelle vollständige Process-Definition für Form 1120.

**Tasks:**
- Alle ~30 Steps definieren
- Button-Images referenzieren
- Fallback-Koordinaten für jeden Step
- Bedingte Logik für Alerts

### Phase 6: Button Assets

Screenshot und Crop der benötigten Buttons.

**Tasks:**
- Anleitung für Button-Cropping
- Verzeichnisstruktur für Assets
- Naming Convention für Images

### Phase 7: Integration

Verbinde ProcessExecutor mit BotController.

**Tasks:**
- bot_controller._run() aktualisieren
- Return-Type Handling (später für 1120S)
- End-to-End Test

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

---

### Task 1: UPDATE requirements.txt

- **IMPLEMENT**: OpenCV und NumPy Dependencies hinzufügen
- **PATTERN**: Bestehende Struktur (one package per line)
- **IMPORTS**: N/A
- **GOTCHA**: opencv-python (nicht opencv-contrib-python)
- **VALIDATE**: `pip install -r requirements.txt`

**Änderung hinzufügen:**
```
opencv-python>=4.8.0
numpy>=1.24.0
```

---

### Task 2: UPDATE config/settings.json

- **IMPLEMENT**: Vision-Section für Template Matching und OCR
- **PATTERN**: Bestehende JSON-Struktur
- **IMPORTS**: N/A
- **GOTCHA**: JSON-Syntax validieren, Pfade mit Forward-Slashes
- **VALIDATE**: `python -c "import json; s=json.load(open('config/settings.json')); assert 'vision' in s; print('OK')"`

**Neue Section hinzufügen:**
```json
"vision": {
  "screenshot_base_path": ".agents/screenshots/buttons",
  "confidence_threshold": 0.8,
  "retry_count": 3,
  "retry_delay_ms": 500,
  "scroll_amount": -3,
  "scroll_max_attempts": 10,
  "scroll_delay_ms": 500
}
```

---

### Task 3: CREATE Directory Structure

- **IMPLEMENT**: Assets-Verzeichnisse für Button-Screenshots
- **PATTERN**: Struktur aus PRD.md
- **IMPORTS**: N/A
- **GOTCHA**: Verzeichnisse müssen existieren bevor Images gespeichert werden
- **VALIDATE**: `dir assets\buttons\common && dir assets\buttons\1120`

**Verzeichnisse erstellen:**
```
assets/
└── buttons/
    ├── common/          # Shared buttons (Continue, Yes, etc.)
    └── 1120/            # 1120-specific buttons
```

---

### Task 4: UPDATE clickbot/__init__.py

- **IMPLEMENT**: Version auf 0.3.0 erhöhen
- **PATTERN**: Bestehende Struktur
- **IMPORTS**: N/A
- **GOTCHA**: Nur __version__ ändern
- **VALIDATE**: `python -c "from clickbot import __version__; print(__version__)"`

---

### Task 5: CREATE clickbot/vision.py - Part 1: Core Functions

- **IMPLEMENT**: Screenshot, Template Matching, Basis-Funktionen
- **PATTERN**: Error Handling aus executor.py, Logging aus allen Modulen
- **IMPORTS**: cv2, numpy, PIL, pyautogui, pytesseract, logging
- **GOTCHA**: cv2.imread() returns BGR, PIL returns RGB — Konvertierung beachten!
- **VALIDATE**: `python -c "from clickbot.vision import take_screenshot; print('OK')"`

**Struktur:**
```python
"""Vision module for hybrid element detection.

Provides:
- Template matching with OpenCV
- Fallback to coordinates
- OCR for text fields
- Checkbox state detection
- Scroll-until-visible pattern
"""

import logging
import time
from pathlib import Path
from typing import Optional, Tuple, List

import cv2
import numpy as np
import pyautogui
from PIL import Image

logger = logging.getLogger(__name__)

# Module configuration
_config = {
    "screenshot_base_path": ".agents/screenshots/buttons",
    "confidence_threshold": 0.8,
    "retry_count": 3,
    "retry_delay_ms": 500,
    "scroll_amount": -3,
    "scroll_max_attempts": 10,
    "scroll_delay_ms": 500,
}


def configure(settings: dict) -> None:
    """Configure vision module from settings.

    Args:
        settings: Settings dict from config/settings.json
    """
    global _config
    vision_settings = settings.get("vision", {})

    _config["screenshot_base_path"] = vision_settings.get("screenshot_base_path", ".agents/screenshots/buttons")
    _config["confidence_threshold"] = vision_settings.get("confidence_threshold", 0.8)
    _config["retry_count"] = vision_settings.get("retry_count", 3)
    _config["retry_delay_ms"] = vision_settings.get("retry_delay_ms", 500)
    _config["scroll_amount"] = vision_settings.get("scroll_amount", -3)
    _config["scroll_max_attempts"] = vision_settings.get("scroll_max_attempts", 10)
    _config["scroll_delay_ms"] = vision_settings.get("scroll_delay_ms", 500)

    logger.debug(f"Vision configured: base_path={_config['screenshot_base_path']}, confidence={_config['confidence_threshold']}")


def take_screenshot(region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
    """Take a screenshot and return as OpenCV-compatible numpy array.

    Args:
        region: Optional (x, y, width, height) tuple for partial screenshot

    Returns:
        Screenshot as BGR numpy array (OpenCV format)
    """
    if region:
        screenshot = pyautogui.screenshot(region=region)
    else:
        screenshot = pyautogui.screenshot()

    # Convert PIL Image to numpy array (RGB)
    img_rgb = np.array(screenshot)
    # Convert RGB to BGR for OpenCV
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    return img_bgr


def load_template(image_path: str) -> Optional[np.ndarray]:
    """Load a template image for matching.

    Args:
        image_path: Path to template image (relative to screenshot_base_path in settings)

    Returns:
        Template as BGR numpy array, or None if not found
    """
    # Build full path using configured base path
    base_path = Path(_config["screenshot_base_path"])
    full_path = base_path / image_path

    if not full_path.exists():
        logger.error(f"Template not found: {full_path}")
        return None

    template = cv2.imread(str(full_path))

    if template is None:
        logger.error(f"Failed to load template: {full_path}")
        return None

    logger.debug(f"Loaded template: {full_path} ({template.shape})")
    return template
```

---

### Task 6: CREATE clickbot/vision.py - Part 2: Template Matching

- **IMPLEMENT**: find_element() mit Template Matching und Fallback
- **PATTERN**: Hybrid Detection Flow aus PRD.md
- **IMPORTS**: Bereits in Part 1
- **GOTCHA**: TM_CCOEFF_NORMED gibt Werte -1 bis 1, Maximum = beste Match
- **VALIDATE**: `python -c "from clickbot.vision import find_element; print('OK')"`

**Hinzufügen:**
```python
def find_element(
    image_path: str,
    confidence: Optional[float] = None,
    fallback_coords: Optional[Tuple[int, int]] = None,
    region: Optional[Tuple[int, int, int, int]] = None
) -> Optional[Tuple[int, int]]:
    """Find an element on screen using template matching.

    Uses hybrid detection:
    1. Try template matching with confidence threshold
    2. Retry up to retry_count times with delay
    3. Fall back to coordinates if provided
    4. Return None if not found and no fallback

    Args:
        image_path: Path to template image (relative to assets/buttons/)
        confidence: Confidence threshold (0.0-1.0), uses config default if None
        fallback_coords: Optional (x, y) fallback coordinates
        region: Optional (x, y, w, h) to limit search area

    Returns:
        (x, y) center coordinates of found element, or None
    """
    if confidence is None:
        confidence = _config["confidence_threshold"]

    # Load template
    template = load_template(image_path)
    if template is None:
        if fallback_coords:
            logger.warning(f"Template not found, using fallback: {fallback_coords}")
            return fallback_coords
        return None

    template_h, template_w = template.shape[:2]

    # Retry loop
    for attempt in range(_config["retry_count"]):
        # Take screenshot
        screenshot = take_screenshot(region)

        # Perform template matching
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        logger.debug(f"Template match attempt {attempt + 1}: confidence={max_val:.3f} (threshold={confidence})")

        if max_val >= confidence:
            # Calculate center of matched region
            center_x = max_loc[0] + template_w // 2
            center_y = max_loc[1] + template_h // 2

            # Adjust for region offset if specified
            if region:
                center_x += region[0]
                center_y += region[1]

            logger.info(f"Element found: {image_path} at ({center_x}, {center_y}) confidence={max_val:.3f}")
            return (center_x, center_y)

        # Wait before retry
        if attempt < _config["retry_count"] - 1:
            time.sleep(_config["retry_delay_ms"] / 1000)

    # Not found after retries
    if fallback_coords:
        logger.warning(f"Element not found after {_config['retry_count']} attempts, using fallback: {fallback_coords}")
        return fallback_coords

    logger.error(f"Element not found: {image_path} (max confidence: {max_val:.3f})")
    return None


def find_and_click(
    image_path: str,
    confidence: Optional[float] = None,
    fallback_coords: Optional[Tuple[int, int]] = None,
    wait_after: float = 2.0
) -> bool:
    """Find an element and click it.

    Args:
        image_path: Path to template image
        confidence: Confidence threshold
        fallback_coords: Fallback coordinates
        wait_after: Seconds to wait after click

    Returns:
        True if element was found and clicked, False otherwise
    """
    from clickbot import executor

    coords = find_element(image_path, confidence, fallback_coords)

    if coords is None:
        return False

    return executor.click(coords[0], coords[1], wait=wait_after)
```

---

### Task 7: CREATE clickbot/vision.py - Part 3: Scroll-until-visible

- **IMPLEMENT**: scroll_until_visible() für Tax Liability Screen
- **PATTERN**: Research-Pattern mit Timeout
- **IMPORTS**: Bereits vorhanden
- **GOTCHA**: Scroll-Region muss in der Mitte des Fensters sein (inneres Scrolling-Fenster)
- **VALIDATE**: `python -c "from clickbot.vision import scroll_until_visible; print('OK')"`

**Hinzufügen:**
```python
def scroll_until_visible(
    image_path: str,
    confidence: Optional[float] = None,
    scroll_x: Optional[int] = None,
    scroll_y: Optional[int] = None,
    direction: str = "down",
    max_attempts: Optional[int] = None
) -> Optional[Tuple[int, int]]:
    """Scroll until an element becomes visible.

    Args:
        image_path: Path to template image to find
        confidence: Confidence threshold
        scroll_x: X coordinate for scroll (center of scroll area)
        scroll_y: Y coordinate for scroll (center of scroll area)
        direction: "down" (negative scroll) or "up" (positive scroll)
        max_attempts: Maximum scroll attempts

    Returns:
        (x, y) coordinates of found element, or None if not found
    """
    from clickbot import executor

    if max_attempts is None:
        max_attempts = _config["scroll_max_attempts"]

    scroll_amount = _config["scroll_amount"]
    if direction == "up":
        scroll_amount = abs(scroll_amount)
    else:
        scroll_amount = -abs(scroll_amount)

    logger.info(f"Scrolling {direction} to find: {image_path}")

    for attempt in range(max_attempts):
        # Check if element is visible
        coords = find_element(image_path, confidence, fallback_coords=None)

        if coords:
            logger.info(f"Element found after {attempt} scrolls")
            return coords

        # Scroll
        logger.debug(f"Scroll attempt {attempt + 1}/{max_attempts}")

        if scroll_x and scroll_y:
            executor.scroll(scroll_amount, x=scroll_x, y=scroll_y)
        else:
            executor.scroll(scroll_amount)

        time.sleep(_config["scroll_delay_ms"] / 1000)

    logger.error(f"Element not found after {max_attempts} scroll attempts: {image_path}")
    return None
```

---

### Task 8: CREATE clickbot/vision.py - Part 4: OCR & Checkbox Functions (100% Template-basiert)

- **IMPLEMENT**: OCR für Textfeld-Prüfung und Checkbox-Erkennung via Template Matching
- **PATTERN**: Template Matching für alles, OCR nur für Textinhalt-Prüfung
- **IMPORTS**: pytesseract
- **GOTCHA**: Checkboxen werden via Template gesucht (nicht feste Region), Textfelder relativ zu Label
- **VALIDATE**: `python -c "from clickbot.vision import is_checkbox_checked_by_template, is_field_empty_by_label; print('OK')"`

**Hinzufügen:**
```python
import pytesseract


def configure_tesseract(settings: dict) -> None:
    """Configure Tesseract OCR path.

    Args:
        settings: Settings dict from config/settings.json
    """
    ocr_settings = settings.get("ocr", {})
    tesseract_path = ocr_settings.get("tesseract_path")

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        logger.debug(f"Tesseract path: {tesseract_path}")


def read_text_region(
    x: int, y: int, width: int, height: int,
    preprocess: bool = True
) -> str:
    """Read text from a screen region using OCR.

    Args:
        x: Region X coordinate
        y: Region Y coordinate
        width: Region width
        height: Region height
        preprocess: Apply preprocessing for better accuracy

    Returns:
        Recognized text (stripped of whitespace)
    """
    # Take screenshot of region
    screenshot = take_screenshot(region=(x, y, width, height))

    if preprocess:
        # Convert to grayscale
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        # Apply threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        img_for_ocr = thresh
    else:
        img_for_ocr = screenshot

    # Convert to PIL for pytesseract
    pil_image = Image.fromarray(img_for_ocr)

    # Run OCR
    text = pytesseract.image_to_string(pil_image, lang='eng')

    result = text.strip()
    logger.debug(f"OCR result for region ({x}, {y}, {width}, {height}): '{result[:50]}' " if len(result) > 50 else f"OCR result: '{result}'")

    return result


def is_checkbox_checked_by_template(
    image_checked: str,
    image_unchecked: str,
    confidence: Optional[float] = None
) -> Tuple[Optional[bool], Optional[Tuple[int, int]]]:
    """Detect if a checkbox is checked by searching for templates on screen.

    Searches the ENTIRE screen for the checkbox templates (no fixed region needed).
    Returns the state and position so we can click it if needed.

    Args:
        image_checked: Path to checked checkbox template (checkbox + label)
        image_unchecked: Path to unchecked checkbox template (checkbox + label)
        confidence: Confidence threshold

    Returns:
        Tuple of (is_checked, position):
        - is_checked: True if checked, False if unchecked, None if neither found
        - position: (x, y) center of found checkbox, or None
    """
    if confidence is None:
        confidence = _config["confidence_threshold"]

    # Take full screenshot
    screenshot = take_screenshot()

    # Search for checked template
    template_checked = load_template(image_checked)
    pos_checked = None
    max_val_checked = 0

    if template_checked is not None:
        result = cv2.matchTemplate(screenshot, template_checked, cv2.TM_CCOEFF_NORMED)
        _, max_val_checked, _, max_loc_checked = cv2.minMaxLoc(result)
        if max_val_checked >= confidence:
            h, w = template_checked.shape[:2]
            pos_checked = (max_loc_checked[0] + w // 2, max_loc_checked[1] + h // 2)

    # Search for unchecked template
    template_unchecked = load_template(image_unchecked)
    pos_unchecked = None
    max_val_unchecked = 0

    if template_unchecked is not None:
        result = cv2.matchTemplate(screenshot, template_unchecked, cv2.TM_CCOEFF_NORMED)
        _, max_val_unchecked, _, max_loc_unchecked = cv2.minMaxLoc(result)
        if max_val_unchecked >= confidence:
            h, w = template_unchecked.shape[:2]
            pos_unchecked = (max_loc_unchecked[0] + w // 2, max_loc_unchecked[1] + h // 2)

    logger.debug(f"Checkbox search: checked={max_val_checked:.3f}, unchecked={max_val_unchecked:.3f}")

    # Determine state based on which template was found with higher confidence
    if max_val_checked >= confidence and max_val_checked > max_val_unchecked:
        logger.info(f"Checkbox is CHECKED at {pos_checked}")
        return (True, pos_checked)
    elif max_val_unchecked >= confidence:
        logger.info(f"Checkbox is UNCHECKED at {pos_unchecked}")
        return (False, pos_unchecked)
    else:
        logger.warning("Checkbox not found on screen")
        return (None, None)


def is_field_empty_by_label(
    label_image: str,
    field_offset_x: int = 150,
    field_offset_y: int = 0,
    field_width: int = 200,
    field_height: int = 25,
    confidence: Optional[float] = None
) -> Tuple[bool, Optional[Tuple[int, int]]]:
    """Check if a text field is empty by finding its label first.

    Finds the label via template matching, then checks the field area
    relative to the label position using OCR.

    Args:
        label_image: Path to label template image (e.g., "Title:" label)
        field_offset_x: Horizontal offset from label to field (pixels)
        field_offset_y: Vertical offset from label to field (pixels)
        field_width: Width of field area to check
        field_height: Height of field area to check
        confidence: Confidence threshold for label detection

    Returns:
        Tuple of (is_empty, field_position):
        - is_empty: True if field is empty
        - field_position: (x, y) of field center for clicking, or None if label not found
    """
    # Find the label
    label_pos = find_element(label_image, confidence, fallback_coords=None)

    if label_pos is None:
        logger.warning(f"Label not found: {label_image}")
        return (True, None)  # Assume empty if we can't find it

    # Calculate field position relative to label
    label_x, label_y = label_pos
    field_x = label_x + field_offset_x
    field_y = label_y + field_offset_y - field_height // 2

    # Read text from field region
    text = read_text_region(field_x, field_y, field_width, field_height)
    is_empty = len(text) == 0

    # Field center for clicking
    field_center = (field_x + field_width // 2, field_y + field_height // 2)

    logger.debug(f"Field check for {label_image}: {'empty' if is_empty else f'has content: {text[:20]}'}")
    return (is_empty, field_center)


def find_and_click_field_by_label(
    label_image: str,
    field_offset_x: int = 150,
    field_offset_y: int = 0,
    confidence: Optional[float] = None
) -> Optional[Tuple[int, int]]:
    """Find a text field by its label and return click position.

    Args:
        label_image: Path to label template image
        field_offset_x: Horizontal offset from label to field
        field_offset_y: Vertical offset from label to field
        confidence: Confidence threshold

    Returns:
        (x, y) position to click for the field, or None if label not found
    """
    label_pos = find_element(label_image, confidence, fallback_coords=None)

    if label_pos is None:
        logger.warning(f"Label not found for field: {label_image}")
        return None

    field_x = label_pos[0] + field_offset_x
    field_y = label_pos[1] + field_offset_y

    logger.debug(f"Field position for {label_image}: ({field_x}, {field_y})")
    return (field_x, field_y)


def verify_screen(
    expected_elements: List[str],
    confidence: Optional[float] = None
) -> bool:
    """Verify we're on the expected screen by checking for elements.

    Args:
        expected_elements: List of image paths that should be visible
        confidence: Confidence threshold

    Returns:
        True if at least one expected element is found
    """
    for element in expected_elements:
        coords = find_element(element, confidence, fallback_coords=None)
        if coords:
            logger.debug(f"Screen verified: found {element}")
            return True

    logger.warning(f"Screen verification failed: none of {expected_elements} found")
    return False
```

---

### Task 9: CREATE clickbot/process_loader.py

- **IMPLEMENT**: Process-JSON Loading und Validierung
- **PATTERN**: load_settings() aus main.py
- **IMPORTS**: json, pathlib, logging, typing
- **GOTCHA**: JSON-Dateien können fehlen oder ungültig sein
- **VALIDATE**: `python -c "from clickbot.process_loader import load_process; print('OK')"`

**Vollständige Datei:**
```python
"""Process definition loader for automation workflows.

Loads and validates process JSON files that define the automation steps.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Required fields in process definition
REQUIRED_PROCESS_FIELDS = ["name", "return_type", "version", "steps"]
REQUIRED_STEP_FIELDS = ["id", "name", "action"]


class ProcessLoadError(Exception):
    """Raised when process loading fails."""
    pass


class ProcessValidationError(Exception):
    """Raised when process validation fails."""
    pass


def load_process(return_type: str) -> Dict[str, Any]:
    """Load a process definition by return type.

    Args:
        return_type: The return type (e.g., "1120", "1120S")

    Returns:
        Process definition dict

    Raises:
        ProcessLoadError: If file not found or invalid JSON
        ProcessValidationError: If process definition is invalid
    """
    process_path = Path(f"config/processes/{return_type}.json")

    if not process_path.exists():
        raise ProcessLoadError(f"Process file not found: {process_path}")

    logger.info(f"Loading process: {process_path}")

    try:
        with open(process_path, "r", encoding="utf-8") as f:
            process = json.load(f)
    except json.JSONDecodeError as e:
        raise ProcessLoadError(f"Invalid JSON in process file: {e}")

    # Validate process
    validate_process(process)

    logger.info(f"Process loaded: {process['name']} with {len(process['steps'])} steps")
    return process


def validate_process(process: Dict[str, Any]) -> None:
    """Validate a process definition.

    Args:
        process: Process definition dict

    Raises:
        ProcessValidationError: If validation fails
    """
    # Check required fields
    for field in REQUIRED_PROCESS_FIELDS:
        if field not in process:
            raise ProcessValidationError(f"Missing required field: {field}")

    # Validate steps
    steps = process.get("steps", [])
    if not steps:
        raise ProcessValidationError("Process has no steps")

    for i, step in enumerate(steps):
        for field in REQUIRED_STEP_FIELDS:
            if field not in step:
                raise ProcessValidationError(f"Step {i+1} missing required field: {field}")

        # Validate action type
        valid_actions = ["click", "double_click", "type", "scroll", "scroll_until_visible",
                        "conditional", "wait", "verify_screen"]
        if step["action"] not in valid_actions:
            raise ProcessValidationError(f"Step {step['id']} has invalid action: {step['action']}")

    logger.debug(f"Process validation passed: {len(steps)} steps")


def get_step(process: Dict[str, Any], step_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific step by ID.

    Args:
        process: Process definition dict
        step_id: Step ID to find

    Returns:
        Step dict or None if not found
    """
    for step in process.get("steps", []):
        if step.get("id") == step_id:
            return step
    return None


def get_static_inputs(process: Dict[str, Any]) -> Dict[str, str]:
    """Get static input values from process.

    Args:
        process: Process definition dict

    Returns:
        Dict of static input values
    """
    return process.get("static_inputs", {})


def get_available_processes() -> List[str]:
    """Get list of available process return types.

    Returns:
        List of return type strings
    """
    processes_dir = Path("config/processes")

    if not processes_dir.exists():
        return []

    return [f.stem for f in processes_dir.glob("*.json")]
```

---

### Task 10: CREATE clickbot/process_executor.py

- **IMPLEMENT**: Step-Ausführung mit Guardrails und Error Handling
- **PATTERN**: bot_controller._run() Pattern, StatusMessage für GUI Updates
- **IMPORTS**: vision, executor, process_loader, sounds, logging, queue
- **GOTCHA**: Muss stop_event prüfen zwischen Steps, keine UI-Updates direkt
- **VALIDATE**: `python -c "from clickbot.process_executor import ProcessExecutor; print('OK')"`

**Vollständige Datei:**
```python
"""Process executor for running automation workflows.

Executes steps defined in process JSON with guardrails and error handling.
"""

import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from clickbot import executor
from clickbot import sounds
from clickbot import vision
from clickbot.bot_controller import StatusMessage
from clickbot.process_loader import load_process, get_static_inputs, ProcessLoadError, ProcessValidationError

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of process execution."""
    success: bool
    steps_completed: int
    total_steps: int
    error_message: Optional[str] = None
    error_step: Optional[int] = None


class ProcessExecutor:
    """Executes automation process steps.

    Handles:
    - Step-by-step execution
    - Guardrails (screen verification)
    - Error handling with sound feedback
    - Status updates via message queue
    """

    def __init__(
        self,
        settings: dict,
        message_queue: queue.Queue,
        stop_event: threading.Event
    ):
        """Initialize the executor.

        Args:
            settings: Settings dict from config/settings.json
            message_queue: Queue for GUI status updates
            stop_event: Event to signal stop
        """
        self.settings = settings
        self.message_queue = message_queue
        self.stop_event = stop_event
        self.current_step = 0
        self.process = None

        # Configure vision module
        vision.configure(settings)
        vision.configure_tesseract(settings)

        logger.debug("ProcessExecutor initialized")

    def execute(self, return_type: str) -> ExecutionResult:
        """Execute a process for the given return type.

        Args:
            return_type: Return type (e.g., "1120")

        Returns:
            ExecutionResult with success status and details
        """
        # Load process
        try:
            self.process = load_process(return_type)
        except (ProcessLoadError, ProcessValidationError) as e:
            self._send_error(f"Failed to load process: {e}")
            return ExecutionResult(
                success=False,
                steps_completed=0,
                total_steps=0,
                error_message=str(e)
            )

        total_steps = len(self.process["steps"])
        static_inputs = get_static_inputs(self.process)

        self._send_status(f"Starting {self.process['name']}")
        self._send_log(f"Process: {return_type} ({total_steps} steps)")

        # Execute steps
        for i, step in enumerate(self.process["steps"]):
            # Check for stop signal
            if self.stop_event.is_set():
                self._send_log("Execution stopped by user")
                return ExecutionResult(
                    success=False,
                    steps_completed=i,
                    total_steps=total_steps,
                    error_message="Stopped by user"
                )

            self.current_step = i + 1
            step_name = step.get("name", f"Step {step['id']}")

            self._send_status(f"Step {self.current_step}/{total_steps}: {step_name}")
            self._send_log(f"Executing: {step_name}")

            # Execute step
            success = self._execute_step(step, static_inputs)

            if not success:
                error_msg = f"Step failed: {step_name}"
                self._send_error(error_msg)
                sounds.play_error()
                return ExecutionResult(
                    success=False,
                    steps_completed=i,
                    total_steps=total_steps,
                    error_message=error_msg,
                    error_step=step["id"]
                )

            # Wait after step (if specified)
            wait_after = step.get("wait_after", self.settings.get("timing", {}).get("default_wait", 2.0))
            if wait_after > 0:
                time.sleep(wait_after)

        # All steps completed
        self._send_log("All steps completed successfully")
        return ExecutionResult(
            success=True,
            steps_completed=total_steps,
            total_steps=total_steps
        )

    def _execute_step(self, step: Dict[str, Any], static_inputs: Dict[str, str]) -> bool:
        """Execute a single step.

        Args:
            step: Step definition dict
            static_inputs: Static input values

        Returns:
            True if step succeeded, False otherwise
        """
        action = step["action"]
        target = step.get("target", {})

        try:
            if action == "click":
                return self._action_click(target)

            elif action == "double_click":
                return self._action_double_click(target)

            elif action == "type":
                return self._action_type(step, static_inputs)

            elif action == "scroll":
                return self._action_scroll(target)

            elif action == "scroll_until_visible":
                return self._action_scroll_until_visible(target)

            elif action == "conditional":
                return self._action_conditional(step, static_inputs)

            elif action == "wait":
                return self._action_wait(step)

            elif action == "verify_screen":
                return self._action_verify_screen(target)

            else:
                logger.error(f"Unknown action: {action}")
                return False

        except Exception as e:
            logger.error(f"Step execution error: {e}", exc_info=True)
            return False

    def _action_click(self, target: Dict[str, Any]) -> bool:
        """Execute click action."""
        image = target.get("image")
        confidence = target.get("confidence")
        fallback = target.get("fallback_coords")

        if fallback:
            fallback = tuple(fallback)

        coords = vision.find_element(image, confidence, fallback)

        if coords is None:
            logger.error(f"Click target not found: {image}")
            return False

        return executor.click(coords[0], coords[1], wait=0)  # wait handled by step

    def _action_double_click(self, target: Dict[str, Any]) -> bool:
        """Execute double-click action."""
        image = target.get("image")
        confidence = target.get("confidence")
        fallback = target.get("fallback_coords")

        if fallback:
            fallback = tuple(fallback)

        coords = vision.find_element(image, confidence, fallback)

        if coords is None:
            logger.error(f"Double-click target not found: {image}")
            return False

        return executor.double_click(coords[0], coords[1], wait=0)

    def _action_type(self, step: Dict[str, Any], static_inputs: Dict[str, str]) -> bool:
        """Execute type action."""
        target = step.get("target", {})
        text_key = step.get("text_key")  # Key in static_inputs
        text_value = step.get("text_value")  # Direct value
        clear_first = step.get("clear_first", True)

        # Get text to type
        if text_key and text_key in static_inputs:
            text = static_inputs[text_key]
        elif text_value:
            text = text_value
        else:
            logger.error("No text specified for type action")
            return False

        # Click field first if target specified
        if target:
            image = target.get("image")
            fallback = target.get("fallback_coords")
            if fallback:
                fallback = tuple(fallback)

            coords = vision.find_element(image, target.get("confidence"), fallback)
            if coords:
                executor.click(coords[0], coords[1], wait=0.5)

        # Clear field if requested
        if clear_first:
            import pyautogui
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.1)

        return executor.type_text(text)

    def _action_scroll(self, target: Dict[str, Any]) -> bool:
        """Execute scroll action."""
        amount = target.get("amount", -3)
        x = target.get("x")
        y = target.get("y")

        return executor.scroll(amount, x, y)

    def _action_scroll_until_visible(self, target: Dict[str, Any]) -> bool:
        """Execute scroll-until-visible action."""
        image = target.get("image")
        confidence = target.get("confidence")
        scroll_x = target.get("scroll_x")
        scroll_y = target.get("scroll_y")
        direction = target.get("scroll_direction", "down")
        max_scrolls = target.get("max_scrolls")

        coords = vision.scroll_until_visible(
            image, confidence, scroll_x, scroll_y, direction, max_scrolls
        )

        return coords is not None

    def _action_conditional(self, step: Dict[str, Any], static_inputs: Dict[str, str]) -> bool:
        """Execute conditional action."""
        condition = step.get("condition", {})
        condition_type = condition.get("type")

        if condition_type == "element_visible":
            # Check if element is visible
            image = condition.get("image")
            confidence = condition.get("confidence")
            is_visible = vision.find_element(image, confidence, fallback_coords=None) is not None

            if is_visible:
                return self._execute_branch(step.get("if_true"), static_inputs)
            else:
                return self._execute_branch(step.get("if_false"), static_inputs)

        elif condition_type == "field_empty_by_label":
            # Check if field is empty using label template (100% screenshot-based)
            label_image = condition.get("label_image")
            field_offset_x = condition.get("field_offset_x", 150)
            field_offset_y = condition.get("field_offset_y", 0)
            field_width = condition.get("field_width", 200)
            field_height = condition.get("field_height", 25)

            is_empty, field_pos = vision.is_field_empty_by_label(
                label_image, field_offset_x, field_offset_y, field_width, field_height
            )

            # Store field position for use in if_true branch
            if field_pos:
                step["_field_position"] = field_pos

            if is_empty:
                return self._execute_branch(step.get("if_true"), static_inputs, field_pos)
            else:
                return self._execute_branch(step.get("if_false"), static_inputs)

        elif condition_type == "checkbox_checked":
            # Check checkbox state using template matching (100% screenshot-based)
            checked_img = condition.get("image_checked")
            unchecked_img = condition.get("image_unchecked")
            confidence = condition.get("confidence")

            is_checked, checkbox_pos = vision.is_checkbox_checked_by_template(
                checked_img, unchecked_img, confidence
            )

            if is_checked is None:
                logger.error("Checkbox not found on screen")
                return False

            if is_checked:
                # Pass position to if_true branch so it can click the checkbox
                return self._execute_branch(step.get("if_true"), static_inputs, checkbox_pos)
            else:
                return self._execute_branch(step.get("if_false"), static_inputs)

        else:
            logger.error(f"Unknown condition type: {condition_type}")
            return False

    def _execute_branch(
        self,
        branch: Any,
        static_inputs: Dict[str, str],
        detected_position: Optional[Tuple[int, int]] = None
    ) -> bool:
        """Execute a conditional branch.

        Args:
            branch: Can be "continue" (do nothing), step dict, or list of steps
            static_inputs: Static input values
            detected_position: Optional (x, y) position from condition check (e.g., checkbox position)

        Returns:
            True if branch executed successfully
        """
        if branch is None or branch == "continue":
            return True

        if isinstance(branch, dict):
            # Single step - inject detected position if action is "click_detected"
            if branch.get("action") == "click_detected" and detected_position:
                return executor.click(detected_position[0], detected_position[1], wait=0)
            elif branch.get("action") == "type_at_detected" and detected_position:
                # Click at detected position, then type
                executor.click(detected_position[0], detected_position[1], wait=0.5)
                text_key = branch.get("text_key")
                text_value = branch.get("text_value")
                clear_first = branch.get("clear_first", True)

                if text_key and text_key in static_inputs:
                    text = static_inputs[text_key]
                elif text_value:
                    text = text_value
                else:
                    return False

                if clear_first:
                    import pyautogui
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.1)
                    pyautogui.press('delete')
                    time.sleep(0.1)

                return executor.type_text(text)
            else:
                return self._execute_step(branch, static_inputs)

        if isinstance(branch, list):
            # Multiple steps
            for step in branch:
                if not self._execute_step(step, static_inputs):
                    return False
            return True

        logger.error(f"Invalid branch type: {type(branch)}")
        return False

    def _action_wait(self, step: Dict[str, Any]) -> bool:
        """Execute wait action."""
        duration = step.get("duration", 1.0)
        time.sleep(duration)
        return True

    def _action_verify_screen(self, target: Dict[str, Any]) -> bool:
        """Execute screen verification."""
        expected = target.get("expected_elements", [])
        confidence = target.get("confidence")

        return vision.verify_screen(expected, confidence)

    # --- Message Helpers ---

    def _send_status(self, message: str) -> None:
        """Send status update to GUI."""
        self.message_queue.put(StatusMessage("status", message))

    def _send_log(self, message: str) -> None:
        """Send log message to GUI."""
        self.message_queue.put(StatusMessage("log", message))

    def _send_error(self, message: str) -> None:
        """Send error message to GUI."""
        self.message_queue.put(StatusMessage("error", message))
```

---

### Task 11: CREATE config/processes/1120.json

- **IMPLEMENT**: Vollständige Process-Definition für Form 1120 (100% Screenshot-basiert)
- **PATTERN**: Schema aus PRD.md, KEINE festen Koordinaten
- **IMPORTS**: N/A
- **GOTCHA**: Alle Elemente werden via Template Matching gefunden, keine Koordinaten nötig
- **VALIDATE**: `python -c "from clickbot.process_loader import load_process; p = load_process('1120'); print(f'{len(p[\"steps\"])} steps')"`

**100% Screenshot-basiert:** Alle Buttons, Checkboxen und Felder werden via Template Matching gefunden. Fallback-Koordinaten sind nur als letzte Option vorhanden.

```json
{
  "name": "Form 1120 E-File Extension",
  "return_type": "1120",
  "version": "2.0",
  "description": "Automated E-File Extension process for Form 1120 - 100% screenshot-based",
  "static_inputs": {
    "officer_title": "president",
    "officer_email": "info@tmaccountant.com",
    "officer_phone": "847850-0085",
    "officer_pin": "12345"
  },
  "steps": [
    {
      "id": 1,
      "name": "close_popup_if_present",
      "action": "conditional",
      "description": "Close Add/Remove State popup if it appears",
      "condition": {
        "type": "element_visible",
        "image": "1120/popup_add_remove_states.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "common/popup_close_x.png" }
      },
      "if_false": "continue",
      "wait_after": 1.0
    },
    {
      "id": 2,
      "name": "click_efile_menu",
      "action": "click",
      "description": "Click E-File in the top menu bar",
      "target": { "image": "common/efile_menu.png" },
      "wait_after": 2.0
    },
    {
      "id": 3,
      "name": "click_submit_electronic_filing",
      "action": "click",
      "description": "Select Submit Electronic Filing Return in popup",
      "target": { "image": "common/submit_electronic_filing.png" },
      "wait_after": 2.0
    },
    {
      "id": 4,
      "name": "select_file_extension",
      "action": "click",
      "description": "Select File Extension option (if not already selected)",
      "target": { "image": "common/file_extension_option_unchecked.png" },
      "wait_after": 1.0
    },
    {
      "id": 5,
      "name": "click_continue_filing",
      "action": "click",
      "description": "Click Continue on Filing screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 6,
      "name": "click_yes_federal_extension",
      "action": "click",
      "description": "Click Yes for Federal Extension",
      "target": { "image": "common/yes_green.png" },
      "wait_after": 2.0
    },
    {
      "id": 7,
      "name": "click_complete_form_7004",
      "action": "click",
      "description": "Click Complete Form 7004 button",
      "target": { "image": "1120/complete_form_7004.png" },
      "wait_after": 2.0
    },
    {
      "id": 8,
      "name": "click_continue_corporation_name",
      "action": "click",
      "description": "Continue on Corporation Name screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 9,
      "name": "check_homeowners_checkbox",
      "action": "conditional",
      "description": "Ensure Homeowners Association checkbox is UNCHECKED - click to uncheck if checked",
      "condition": {
        "type": "checkbox_checked",
        "image_checked": "1120/checkbox_homeowners_checked.png",
        "image_unchecked": "1120/checkbox_homeowners_unchecked.png"
      },
      "if_true": { "action": "click_detected" },
      "if_false": "continue",
      "wait_after": 0.5
    },
    {
      "id": 10,
      "name": "click_continue_homeowners",
      "action": "click",
      "description": "Continue on Homeowners screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 11,
      "name": "click_continue_address",
      "action": "click",
      "description": "Continue on Address screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 12,
      "name": "click_continue_federal_id",
      "action": "click",
      "description": "Continue on Federal ID Number screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 13,
      "name": "click_continue_fiscal_year",
      "action": "click",
      "description": "Continue on Fiscal Year screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 14,
      "name": "click_continue_todays_date",
      "action": "click",
      "description": "Continue on Today's Date screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 15,
      "name": "check_no_office_checkbox",
      "action": "conditional",
      "description": "Ensure 'No office or place of business in the United States' checkbox is UNCHECKED",
      "condition": {
        "type": "checkbox_checked",
        "image_checked": "1120/checkbox_no_office_checked.png",
        "image_unchecked": "1120/checkbox_no_office_unchecked.png"
      },
      "if_true": { "action": "click_detected" },
      "if_false": "continue",
      "wait_after": 0.5
    },
    {
      "id": 16,
      "name": "click_continue_no_office",
      "action": "click",
      "description": "Continue on No Office screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 17,
      "name": "check_section_checkbox",
      "action": "conditional",
      "description": "Ensure Section 1.6081-5 checkbox is UNCHECKED",
      "condition": {
        "type": "checkbox_checked",
        "image_checked": "1120/checkbox_section_checked.png",
        "image_unchecked": "1120/checkbox_section_unchecked.png"
      },
      "if_true": { "action": "click_detected" },
      "if_false": "continue",
      "wait_after": 0.5
    },
    {
      "id": 18,
      "name": "click_continue_section",
      "action": "click",
      "description": "Continue on Section screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 19,
      "name": "scroll_tax_liability",
      "action": "scroll_until_visible",
      "description": "Scroll down in Tax Liability screen until Continue button is visible (scroll in screen center)",
      "target": {
        "image": "common/continue_blue.png",
        "scroll_x": 960,
        "scroll_y": 540,
        "scroll_direction": "down",
        "max_scrolls": 10
      },
      "wait_after": 1.0
    },
    {
      "id": 20,
      "name": "click_continue_tax_liability",
      "action": "click",
      "description": "Continue on Tax Liability screen (after scroll)",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 21,
      "name": "click_continue_payment",
      "action": "click",
      "description": "Continue on Payment Amount screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 22,
      "name": "click_efile_form_7004",
      "action": "click",
      "description": "Click E-File Form 7004 green button (Print Form 7004 screen)",
      "target": { "image": "1120/efile_form_7004.png" },
      "wait_after": 2.0
    },
    {
      "id": 23,
      "name": "click_continue_acknowledgment",
      "action": "click",
      "description": "Continue on Acknowledgment Status screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 24,
      "name": "check_and_fill_officer_title",
      "action": "conditional",
      "description": "Fill Officer Title if empty (Signing Officer Information screen)",
      "condition": {
        "type": "field_empty_by_label",
        "label_image": "1120/label_title.png",
        "field_offset_x": 120,
        "field_width": 200,
        "field_height": 25
      },
      "if_true": {
        "action": "type_at_detected",
        "text_key": "officer_title",
        "clear_first": true
      },
      "if_false": "continue",
      "wait_after": 0.5
    },
    {
      "id": 25,
      "name": "check_and_fill_officer_email",
      "action": "conditional",
      "description": "Fill Officer Email if empty",
      "condition": {
        "type": "field_empty_by_label",
        "label_image": "1120/label_email.png",
        "field_offset_x": 120,
        "field_width": 250,
        "field_height": 25
      },
      "if_true": {
        "action": "type_at_detected",
        "text_key": "officer_email",
        "clear_first": true
      },
      "if_false": "continue",
      "wait_after": 0.5
    },
    {
      "id": 26,
      "name": "check_and_fill_officer_phone",
      "action": "conditional",
      "description": "Fill Officer Phone if empty",
      "condition": {
        "type": "field_empty_by_label",
        "label_image": "1120/label_phone.png",
        "field_offset_x": 120,
        "field_width": 150,
        "field_height": 25
      },
      "if_true": {
        "action": "type_at_detected",
        "text_key": "officer_phone",
        "clear_first": true
      },
      "if_false": "continue",
      "wait_after": 0.5
    },
    {
      "id": 27,
      "name": "click_continue_officer_info",
      "action": "click",
      "description": "Continue on Signing Officer Information screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 28,
      "name": "enter_officer_pin",
      "action": "conditional",
      "description": "Enter Officer PIN (Officer's Signature screen)",
      "condition": {
        "type": "field_empty_by_label",
        "label_image": "1120/label_pin.png",
        "field_offset_x": 120,
        "field_width": 100,
        "field_height": 25
      },
      "if_true": {
        "action": "type_at_detected",
        "text_key": "officer_pin",
        "clear_first": true
      },
      "if_false": "continue",
      "wait_after": 0.5
    },
    {
      "id": 29,
      "name": "click_continue_pin",
      "action": "click",
      "description": "Continue after PIN entry",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 30,
      "name": "click_continue_ero_signature",
      "action": "click",
      "description": "Continue on ERO Signature screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 2.0
    },
    {
      "id": 31,
      "name": "click_start_form_7004_alerts",
      "action": "click",
      "description": "Click Start Form 7004 Alerts button (Federal E-File Alerts screen)",
      "target": { "image": "1120/start_form_7004_alerts.png" },
      "wait_after": 3.0
    },
    {
      "id": 32,
      "name": "handle_alerts_result",
      "action": "conditional",
      "description": "Check if 'Passed Alerts' or 'Error/Omission' - different actions for each",
      "condition": {
        "type": "element_visible",
        "image": "common/passed_alerts.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "common/continue_blue.png" }
      },
      "if_false": {
        "action": "click",
        "description": "Click Clients button to return to base (Error/Omission case)",
        "target": { "image": "common/clients_button.png" }
      },
      "wait_after": 2.0
    },
    {
      "id": 33,
      "name": "click_submit_efile",
      "action": "conditional",
      "description": "Click Submit E-File button if visible (only after passed alerts)",
      "condition": {
        "type": "element_visible",
        "image": "1120/submit_efile.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "1120/submit_efile.png" }
      },
      "if_false": "continue",
      "wait_after": 2.0
    },
    {
      "id": 34,
      "name": "click_continue_green_confirmation",
      "action": "conditional",
      "description": "Click GREEN Continue (NOT blue!) on confirmation screen",
      "condition": {
        "type": "element_visible",
        "image": "common/continue_green.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "common/continue_green.png" }
      },
      "if_false": "continue",
      "wait_after": 2.0
    },
    {
      "id": 35,
      "name": "click_new_return",
      "action": "conditional",
      "description": "Click New Return button (Filing Complete screen)",
      "condition": {
        "type": "element_visible",
        "image": "common/new_return.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "common/new_return.png" }
      },
      "if_false": "continue",
      "wait_after": 2.0
    },
    {
      "id": 36,
      "name": "close_add_client_popup",
      "action": "conditional",
      "description": "Close Add Client popup if present",
      "condition": {
        "type": "element_visible",
        "image": "common/popup_close_x.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "common/popup_close_x.png" }
      },
      "if_false": "continue",
      "wait_after": 2.0
    }
  ]
}
```

---

### Task 12: UPDATE clickbot/bot_controller.py

- **IMPLEMENT**: Integration von ProcessExecutor in _run()
- **PATTERN**: Bestehende Struktur, StatusMessage weiter nutzen
- **IMPORTS**: from clickbot.process_executor import ProcessExecutor, ExecutionResult
- **GOTCHA**: return_type muss irgendwo herkommen (für jetzt hardcoded "1120")
- **VALIDATE**: `python -c "from clickbot.bot_controller import BotController; print('OK')"`

**Änderungen in _run():**
```python
def _run(self) -> None:
    """Main bot loop - runs in worker thread.

    WARNING: Do NOT update any UI elements from this method!
    Use self.message_queue.put() to send updates to GUI.
    """
    from clickbot.process_executor import ProcessExecutor

    logger.info("Bot worker thread running")
    self.message_queue.put(StatusMessage("status", "Bot running"))

    # Create executor
    executor = ProcessExecutor(
        self.settings,
        self.message_queue,
        self.stop_event
    )

    # Execute process for 1120 (hardcoded for Phase 3)
    # TODO: In Phase 4, return_type will be detected via OCR
    return_type = "1120"

    result = executor.execute(return_type)

    if result.success:
        self.message_queue.put(StatusMessage("complete",
            f"Completed! {result.steps_completed}/{result.total_steps} steps"))
        sounds.play_complete()
    else:
        if result.error_message != "Stopped by user":
            self.message_queue.put(StatusMessage("error", result.error_message or "Unknown error"))
            sounds.play_error()

    self.state = BotState.IDLE
    logger.info("Bot worker thread finished")
```

---

### Task 13: VERIFY Screenshot Assets ✅

- **IMPLEMENT**: Alle Screenshots sind bereits vorhanden
- **PATTERN**: PNG-Dateien in `.agents/screenshots/buttons/`
- **IMPORTS**: N/A
- **GOTCHA**: Pfad wird aus `settings.json` → `vision.screenshot_base_path` geladen
- **VALIDATE**: `python -c "from pathlib import Path; print(len(list(Path('.agents/screenshots/buttons').rglob('*.png'))), 'screenshots found')"`

**Screenshot-Verzeichnis:** `.agents/screenshots/buttons/` (konfigurierbar in settings.json)

---

## VORHANDENE SCREENSHOTS (27 Dateien) ✅

### Common (12 Dateien)

| Dateiname | Typ | Verwendung |
|-----------|-----|------------|
| `common/popup_close_x.png` | Button | X zum Schließen von Popups |
| `common/efile_menu.png` | Button | E-File Menüeintrag |
| `common/submit_electronic_filing.png` | Button | Submit Electronic Filing Return |
| `common/file_extension_option_unchecked.png` | Radio | File Extension (nicht ausgewählt) |
| `common/file_extension_option_checked.png` | Radio | File Extension (ausgewählt) |
| `common/continue_blue.png` | Button | Blauer Continue Button |
| `common/continue_green.png` | Button | Grüner Continue Button |
| `common/yes_green.png` | Button | Grüner Yes Button |
| `common/start_alerts.png` | Button | Generischer Start Alerts Button |
| `common/passed_alerts.png` | **Text** | "Passed Alerts" Erkennung (kein Klick!) |
| `common/clients_button.png` | Button | Clients Button oben links |
| `common/new_return.png` | Button | New Return Button |

### 1120-Spezifisch (15 Dateien)

| Dateiname | Typ | Verwendung |
|-----------|-----|------------|
| `1120/popup_add_remove_states.png` | Popup | Add/Remove States Popup Erkennung |
| `1120/complete_form_7004.png` | Button | Complete Form 7004 Button |
| `1120/efile_form_7004.png` | Button | E-File Form 7004 Button |
| `1120/start_form_7004_alerts.png` | Button | Start Form 7004 Alerts Button |
| `1120/submit_efile.png` | Button | Submit E-File Button |
| `1120/checkbox_homeowners_unchecked.png` | Checkbox | ☐ Homeowners Association |
| `1120/checkbox_homeowners_checked.png` | Checkbox | ☑ Homeowners Association |
| `1120/checkbox_no_office_unchecked.png` | Checkbox | ☐ No office in US |
| `1120/checkbox_no_office_checked.png` | Checkbox | ☑ No office in US |
| `1120/checkbox_section_unchecked.png` | Checkbox | ☐ Section 1.6081-5 |
| `1120/checkbox_section_checked.png` | Checkbox | ☑ Section 1.6081-5 |
| `1120/label_title.png` | Label | "Title:" für OCR |
| `1120/label_email.png` | Label | "Email address:" für OCR |
| `1120/label_phone.png` | Label | "Phone number:" für OCR |
| `1120/label_pin.png` | Label | "Officer's PIN:" für OCR |

---

**Gesamtzahl Screenshots: 27** ✅

| Kategorie | Anzahl |
|-----------|--------|
| Common | 12 |
| 1120 Buttons | 5 |
| 1120 Checkboxen | 6 |
| 1120 Labels | 4 |
| **Total** | **27** |

---

### Task 14: CREATE tests/manual/test_phase3.py

- **IMPLEMENT**: Manueller Integrationstest für Phase 3
- **PATTERN**: test_phase1.py Struktur
- **IMPORTS**: Alle neuen Module
- **GOTCHA**: Braucht echte TaxAct-Instanz für vollständigen Test
- **VALIDATE**: `python tests/manual/test_phase3.py`

**Test-Datei:**
```python
"""Phase 3 Integration Test - Single Iteration (1120).

This test validates:
1. All new modules import correctly
2. Vision module can take screenshots
3. Process loader can load 1120.json
4. Process executor initializes

For FULL testing, TaxAct must be open with a 1120 client selected.
"""

import sys
from pathlib import Path


def main():
    print("\n" + "=" * 50)
    print("Phase 3 Integration Test")
    print("=" * 50)

    # Test 1: Import all new modules
    print("\n[1/6] Testing module imports...")
    try:
        from clickbot import vision
        from clickbot import process_loader
        from clickbot import process_executor
        print("  OK: All new modules imported successfully")
    except ImportError as e:
        print(f"  FAIL: Import error: {e}")
        return 1

    # Test 2: Load settings
    print("\n[2/6] Testing settings with vision config...")
    try:
        import json
        with open("config/settings.json", "r") as f:
            settings = json.load(f)

        assert "vision" in settings, "Missing 'vision' section"
        print(f"  OK: Vision config loaded (confidence={settings['vision']['confidence_threshold']})")
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Test 3: Vision module functions
    print("\n[3/6] Testing vision.take_screenshot()...")
    try:
        vision.configure(settings)
        screenshot = vision.take_screenshot()
        print(f"  OK: Screenshot captured ({screenshot.shape})")
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Test 4: Process loader
    print("\n[4/6] Testing process_loader.load_process('1120')...")
    try:
        process = process_loader.load_process("1120")
        print(f"  OK: Process loaded: {process['name']} ({len(process['steps'])} steps)")
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Test 5: Process executor initialization
    print("\n[5/6] Testing ProcessExecutor initialization...")
    try:
        import queue
        import threading

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        executor = process_executor.ProcessExecutor(settings, msg_queue, stop_event)
        print("  OK: ProcessExecutor initialized")
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Test 6: Check assets directory
    print("\n[6/6] Checking assets directory structure...")
    assets_common = Path("assets/buttons/common")
    assets_1120 = Path("assets/buttons/1120")

    if assets_common.exists() and assets_1120.exists():
        common_files = list(assets_common.glob("*.png"))
        files_1120 = list(assets_1120.glob("*.png"))
        print(f"  OK: Assets directories exist")
        print(f"      common/: {len(common_files)} PNG files")
        print(f"      1120/: {len(files_1120)} PNG files")

        if len(common_files) == 0:
            print("  WARNING: No button screenshots in common/ - need to create them!")
    else:
        print("  WARNING: Assets directories missing - run 'mkdir assets\\buttons\\common assets\\buttons\\1120'")

    # Summary
    print("\n" + "=" * 50)
    print("Phase 3 Basic Tests: PASSED")
    print("=" * 50)
    print("\nNEXT STEPS:")
    print("1. Create button screenshots in assets/buttons/")
    print("2. Calibrate coordinates in config/processes/1120.json")
    print("3. Test with real TaxAct instance")
    print("\nTo run full automation test:")
    print("  python -m clickbot.gui")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## TESTING STRATEGY

### Unit Tests

Die neuen Module haben viele externe Dependencies (OpenCV, pyautogui, Tesseract). Unit Tests sollten diese mocken.

**Beispiel test_vision.py:**
```python
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

class TestVision:
    @patch('clickbot.vision.pyautogui')
    def test_take_screenshot_returns_numpy_array(self, mock_pyautogui):
        from clickbot import vision

        # Mock screenshot
        mock_img = MagicMock()
        mock_img.__array__ = lambda: np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_pyautogui.screenshot.return_value = mock_img

        result = vision.take_screenshot()

        assert isinstance(result, np.ndarray)
        assert result.shape == (1080, 1920, 3)
```

### Integration Tests

- `test_phase3.py` prüft Module-Integration
- Manueller Test mit echter TaxAct-Instanz erforderlich

### Manual Testing Checklist

**Before Full Test:**
- [ ] TaxAct 2025 geöffnet
- [ ] Client mit Return Type 1120 und leerem Fed EF Status vorhanden
- [ ] TaxAct auf Primary Monitor
- [ ] Button-Screenshots erstellt und in assets/buttons/
- [ ] Koordinaten in 1120.json kalibriert

**During Test:**
- [ ] GUI startet mit `python -m clickbot.gui`
- [ ] Start-Button → Countdown → Bot startet
- [ ] Log zeigt Step-Fortschritt
- [ ] Klicks landen auf richtigen Buttons
- [ ] Scroll auf Tax Liability Screen funktioniert
- [ ] Officer-Felder werden korrekt gefüllt (wenn leer)
- [ ] Bei Error/Omission → zurück zur Base
- [ ] Bei Passed → Submit durchläuft
- [ ] Am Ende zurück in Client Manager

---

## VALIDATION COMMANDS

### Level 1: Syntax & Dependencies

```bash
pip install -r requirements.txt
python -m py_compile clickbot/vision.py
python -m py_compile clickbot/process_loader.py
python -m py_compile clickbot/process_executor.py
```

### Level 2: Import Tests

```bash
python -c "import cv2; print(f'OpenCV {cv2.__version__} OK')"
python -c "import numpy; print(f'NumPy {numpy.__version__} OK')"
python -c "from clickbot.vision import configure, take_screenshot, find_element; print('vision.py OK')"
python -c "from clickbot.process_loader import load_process; print('process_loader.py OK')"
python -c "from clickbot.process_executor import ProcessExecutor; print('process_executor.py OK')"
```

### Level 3: Configuration Tests

```bash
python -c "import json; s=json.load(open('config/settings.json')); assert 'vision' in s; print('Settings OK')"
python -c "from clickbot.process_loader import load_process; p=load_process('1120'); print(f'{len(p[\"steps\"])} steps OK')"
```

### Level 4: Integration Test

```bash
python tests/manual/test_phase3.py
```

### Level 5: Manual Full Test

```bash
python -m clickbot.gui
# Then manually test with TaxAct
```

---

## ACCEPTANCE CRITERIA

- [ ] OpenCV und NumPy installiert und funktionieren
- [ ] vision.py kann Screenshots aufnehmen
- [ ] vision.py kann Template Matching durchführen
- [ ] vision.py kann Textfelder per OCR prüfen
- [ ] process_loader.py lädt 1120.json erfolgreich
- [ ] process_executor.py führt Steps aus
- [ ] bot_controller._run() verwendet ProcessExecutor
- [ ] GUI zeigt Step-Fortschritt im Log
- [ ] Scroll-until-visible funktioniert
- [ ] Bedingte Logik (Checkbox, Field empty, Alerts) funktioniert
- [ ] Bei Fehler: Error-Sound + Bot stoppt
- [ ] Alle Validation Commands erfolgreich

---

## COMPLETION CHECKLIST

- [ ] requirements.txt aktualisiert (opencv-python, numpy)
- [ ] config/settings.json hat "vision" Section
- [ ] assets/buttons/ Verzeichnisse existieren
- [ ] clickbot/vision.py erstellt und getestet
- [ ] clickbot/process_loader.py erstellt und getestet
- [ ] clickbot/process_executor.py erstellt und getestet
- [ ] config/processes/1120.json erstellt
- [ ] clickbot/bot_controller.py aktualisiert
- [ ] tests/manual/test_phase3.py erstellt
- [ ] Alle Import-Tests erfolgreich
- [ ] Button-Screenshots erstellt
- [ ] Koordinaten kalibriert
- [ ] Manueller End-to-End Test erfolgreich

---

## NOTES

### Design-Entscheidungen

1. **Hybrid Detection (Image + Fallback)**: Robuster als reine Koordinaten, aber mit Fallback für Zuverlässigkeit

2. **Separate Module**: vision.py, process_loader.py, process_executor.py — klare Trennung der Verantwortlichkeiten

3. **JSON-basierte Process Definition**: Änderungen ohne Code-Anpassung möglich

4. **Bedingte Logik in JSON**: Erlaubt komplexe Workflows (Error/Omission Handling)

5. **TM_CCOEFF_NORMED**: Standard-Methode für Template Matching, robust gegenüber Beleuchtung

### Bekannte Limitierungen

- Koordinaten sind PLACEHOLDER — müssen mit echten Screenshots kalibriert werden
- Return-Type ist hardcoded "1120" — OCR-Erkennung kommt in Phase 4
- Keine Duplikat-Vermeidung — kommt in Phase 6

### Nächste Phasen

**Phase 4 (OCR & Intelligence):**
- Return-Type automatisch aus Client-Tabelle erkennen
- Fed EF Status prüfen (leer = bearbeiten)
- Client-Name per OCR lesen

**Phase 5 (1120S Prozess):**
- 1120S.json erstellen
- Unterschiedliche Klickabfolge

**Phase 6 (Loop Mode):**
- Mehrere Clients nacheinander
- Client-Tracking (keine Duplikate)
- Scrollen in Client-Liste

### Risiken

1. **Template Matching Genauigkeit**: Buttons könnten je nach TaxAct-Version leicht anders aussehen
2. **Koordinaten-Abhängigkeit**: Fallback-Koordinaten müssen stimmen
3. **Tesseract OCR Genauigkeit**: Preprocessing wichtig für gute Ergebnisse
4. **Timing**: TaxAct könnte unterschiedlich schnell reagieren

### Button Screenshot Anleitung

1. TaxAct öffnen und zum gewünschten Screen navigieren
2. Windows Snipping Tool (Win+Shift+S) verwenden
3. Nur den Button ausschneiden (mit etwas Rand)
4. Als PNG in assets/buttons/common/ oder assets/buttons/1120/ speichern
5. Dateiname gemäß Liste in Task 13

---

## CONFIDENCE SCORE: 10/10 ✅

**Gründe:**
- Vollständige Module-Implementierungen
- 100% Screenshot-basiert — KEINE Koordinaten-Kalibrierung nötig!
- **Alle 27 Screenshots vorhanden** in `.agents/screenshots/buttons/`
- Klare Patterns aus vorheriger Phase übernommen
- JSON-basierte Konfiguration flexibel
- Robustes Hybrid-System mit Template Matching
- Checkboxen und Felder werden automatisch gefunden
- Screenshot-Pfad konfigurierbar via `settings.json`

**Alles bereit für Implementierung!**

**Verbesserungen:**
- Keine festen Koordinaten mehr
- Checkboxen werden via Template gefunden und Position zurückgegeben
- Textfelder werden relativ zu Labels gefunden
- Scroll funktioniert mit Bildschirmmitte (960, 540)
- Screenshot-Pfad ist konfigurierbar

---

*Plan erstellt: 2026-02-06*
*Basierend auf PRD v2.2 und User-Workflow-Beschreibung*
