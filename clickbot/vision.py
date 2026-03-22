"""Vision module for hybrid element detection.

Provides:
- Template matching with OpenCV
- Fallback to coordinates
- OCR for text fields
- Checkbox state detection
- Scroll-until-visible pattern
"""

import logging
import threading
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

import cv2
import numpy as np
import pyautogui
import pytesseract
from PIL import Image

from clickbot import paths

logger = logging.getLogger(__name__)

# Module configuration
_config = {
    "screenshot_base_path": str(paths.get_buttons_dir()),
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

    # Resolve screenshot_base_path against bundle dir for frozen builds
    raw_base = vision_settings.get("screenshot_base_path", ".agents/screenshots/buttons")
    base_path = Path(raw_base)
    if not base_path.is_absolute():
        base_path = paths.get_bundle_dir() / base_path
    _config["screenshot_base_path"] = str(base_path)

    _config["confidence_threshold"] = vision_settings.get("confidence_threshold", 0.8)
    _config["retry_count"] = vision_settings.get("retry_count", 3)
    _config["retry_delay_ms"] = vision_settings.get("retry_delay_ms", 500)
    _config["scroll_amount"] = vision_settings.get("scroll_amount", -3)
    _config["scroll_max_attempts"] = vision_settings.get("scroll_max_attempts", 10)
    _config["scroll_delay_ms"] = vision_settings.get("scroll_delay_ms", 500)

    logger.debug(f"Vision configured: base_path={_config['screenshot_base_path']}, confidence={_config['confidence_threshold']}")


def configure_tesseract(settings: dict) -> None:
    """Configure Tesseract OCR path.

    In frozen (exe) mode: uses bundled tesseract from tesseract_bundle/.
    In dev mode: uses path from settings.json.

    Args:
        settings: Settings dict from config/settings.json
    """
    if paths.is_frozen():
        # Use bundled tesseract
        bundled = paths.get_tesseract_path()
        if bundled.exists():
            pytesseract.pytesseract.tesseract_cmd = str(bundled)
            logger.debug(f"Tesseract (bundled): {bundled}")
            return
        logger.warning(f"Bundled tesseract not found: {bundled}")

    # Dev mode: use path from settings
    ocr_settings = settings.get("ocr", {})
    tesseract_path = ocr_settings.get("tesseract_path")

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        logger.debug(f"Tesseract path: {tesseract_path}")


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


def load_template(
    image_path: str,
    base_path: Optional[str] = None
) -> Optional[np.ndarray]:
    """Load a template image for matching.

    Args:
        image_path: Path to template image (relative to base_path)
        base_path: Override base path (default: screenshot_base_path from config)

    Returns:
        Template as BGR numpy array, or None if not found
    """
    # Build full path using configured base path or override
    root = Path(base_path) if base_path else Path(_config["screenshot_base_path"])
    full_path = root / image_path

    if not full_path.exists():
        logger.error(f"Template not found: {full_path}")
        return None

    template = cv2.imread(str(full_path))

    if template is None:
        logger.error(f"Failed to load template: {full_path}")
        return None

    logger.debug(f"Loaded template: {full_path} ({template.shape})")
    return template


def debug_match_confidence(
    image_path: str,
    base_path: Optional[str] = None
) -> Tuple[Optional[float], bool, str]:
    """Check template match confidence for debugging.

    Takes a screenshot and returns the best match confidence without
    any retry logic. Used to diagnose why verify_next fails.

    Args:
        image_path: Path to template image (relative to base_path)
        base_path: Override base path for template loading

    Returns:
        Tuple of (max_confidence, template_loaded, full_path_str):
        - max_confidence: Best match score (0.0-1.0), or None if template not loaded
        - template_loaded: Whether the template file was found and loaded
        - full_path_str: The resolved full path that was checked
    """
    root = Path(base_path) if base_path else Path(_config["screenshot_base_path"])
    full_path = root / image_path
    full_path_str = str(full_path)

    if not full_path.exists():
        return (None, False, full_path_str)

    template = cv2.imread(full_path_str)
    if template is None:
        return (None, False, full_path_str)

    screenshot = take_screenshot()
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    template_h, template_w = template.shape[:2]
    screenshot_h, screenshot_w = screenshot.shape[:2]
    logger.debug(
        f"debug_match: {image_path} -> confidence={max_val:.4f}, "
        f"template={template_w}x{template_h}, screen={screenshot_w}x{screenshot_h}, "
        f"best_loc={max_loc}"
    )

    return (max_val, True, full_path_str)


def find_element(
    image_path: str,
    confidence: Optional[float] = None,
    fallback_coords: Optional[Tuple[int, int]] = None,
    region: Optional[Tuple[int, int, int, int]] = None,
    retry_count: Optional[int] = None,
    base_path: Optional[str] = None
) -> Optional[Tuple[int, int]]:
    """Find an element on screen using template matching.

    Uses hybrid detection:
    1. Try template matching with confidence threshold
    2. Retry up to retry_count times with delay
    3. Fall back to coordinates if provided
    4. Return None if not found and no fallback

    Args:
        image_path: Path to template image (relative to base_path)
        confidence: Confidence threshold (0.0-1.0), uses config default if None
        fallback_coords: Optional (x, y) fallback coordinates
        region: Optional (x, y, w, h) to limit search area
        retry_count: Override retry count (default: config value)
        base_path: Override base path for template loading

    Returns:
        (x, y) center coordinates of found element, or None
    """
    if confidence is None:
        confidence = _config["confidence_threshold"]

    # Load template
    template = load_template(image_path, base_path=base_path)
    if template is None:
        if fallback_coords:
            logger.warning(f"Template not found, using fallback: {fallback_coords}")
            return fallback_coords
        return None

    template_h, template_w = template.shape[:2]
    max_val = 0

    # Retry loop
    retries = retry_count if retry_count is not None else _config["retry_count"]
    for attempt in range(retries):
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
        if attempt < retries - 1:
            time.sleep(_config["retry_delay_ms"] / 1000)

    # Not found after retries
    if fallback_coords:
        logger.warning(f"Element not found after {retries} attempts, using fallback: {fallback_coords}")
        return fallback_coords

    logger.error(f"Element not found: {image_path} (max confidence: {max_val:.3f})")
    return None


def wait_for_element(
    image_path: str,
    timeout: float = 10.0,
    poll_interval: float = 0.333,
    confidence: Optional[float] = None,
    region: Optional[Tuple[int, int, int, int]] = None,
    base_path: Optional[str] = None,
    stop_event: Optional["threading.Event"] = None
) -> Optional[Tuple[int, int]]:
    """Poll screen until element appears or timeout.

    Uses SikuliX-style polling (default 3Hz scan rate).
    Unlike find_element(), does NOT use fallback_coords.

    Args:
        image_path: Path to template image
        timeout: Maximum seconds to wait
        poll_interval: Seconds between checks (default ~3Hz)
        confidence: Confidence threshold
        region: Optional search region
        base_path: Override base path for template loading
        stop_event: Optional threading.Event to abort early on stop signal

    Returns:
        (x, y) if found, None on timeout or stop
    """
    deadline = time.time() + timeout
    attempts = 0
    while time.time() < deadline:
        # Check stop signal
        if stop_event is not None and stop_event.is_set():
            logger.debug(f"wait_for_element: aborted by stop signal after {attempts} polls")
            return None

        attempts += 1
        coords = find_element(
            image_path, confidence,
            fallback_coords=None,
            region=region,
            retry_count=1,
            base_path=base_path
        )
        if coords is not None:
            logger.debug(f"wait_for_element: found {image_path} after {attempts} polls")
            return coords
        time.sleep(poll_interval)

    logger.debug(f"wait_for_element: timeout after {attempts} polls for {image_path}")
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
        # Convert to grayscale + Otsu threshold (aggressive binarization)
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        img_for_ocr = thresh
    else:
        # Convert to grayscale only (matches what Tesseract does internally,
        # avoids BGR/RGB color swap that corrupts OCR with raw BGR arrays)
        img_for_ocr = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    # Convert to PIL for pytesseract
    pil_image = Image.fromarray(img_for_ocr)

    # Run OCR
    text = pytesseract.image_to_string(pil_image, lang='eng')

    result = text.strip()
    if len(result) > 50:
        logger.debug(f"OCR result for region ({x}, {y}, {width}, {height}): '{result[:50]}...'")
    else:
        logger.debug(f"OCR result: '{result}'")

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


# =============================================================================
# Client Table Scanning Functions
# =============================================================================

@dataclass
class ClientRow:
    """Data from a single client table row."""
    row_index: int
    y_position: int
    client_name: str
    return_type: str
    fed_ef_status: str
    client_id: str = ""  # SSN/EIN for composite-key CSV lookup


import re

# Pattern: any digit + "120" + optional trailing character
# Matches: 1120, 1120S, 4120, 41205, 11208, etc.
_RETURN_TYPE_1120_PATTERN = re.compile(r'\d120(.)?')

# Pattern: 1040 (OCR may misread as 4040, 1O40, etc.)
_RETURN_TYPE_1040_PATTERN = re.compile(r'[14]\d?40')


def normalize_return_type(ocr_value: str) -> str:
    """Normalize OCR-read return type to correct process name.

    OCR commonly misreads characters in the return type column:
    - First "1" misread as "4" (4120 -> 1120)
    - Trailing "S" misread as "5" or "8" (11205/11208 -> 1120S)
    - "1040" misread as "4040" or similar

    Args:
        ocr_value: Raw OCR result for return type

    Returns:
        Normalized return type: "1120", "1120S", or "1040"
    """
    # Clean up OCR result: take first non-empty line
    lines = [line.strip() for line in ocr_value.split('\n') if line.strip()]
    cleaned = lines[0].strip() if lines else ""

    # Strip all whitespace for matching
    compact = cleaned.replace(" ", "")

    # Check for 1040 first (before 1120, since "1040" won't match \d120)
    if _RETURN_TYPE_1040_PATTERN.search(compact):
        logger.debug(f"Return type '{cleaned}' -> '1040'")
        return "1040"

    match = _RETURN_TYPE_1120_PATTERN.search(compact)
    if match:
        trailing = match.group(1)
        if trailing:
            logger.debug(f"Return type '{cleaned}' -> '1120S' (trailing char: '{trailing}')")
            return "1120S"
        else:
            logger.debug(f"Return type '{cleaned}' -> '1120' (no trailing char)")
            return "1120"

    logger.debug(f"Return type not recognized: '{cleaned}'")
    return cleaned


def get_column_positions(
    extra_columns: Optional[List[str]] = None
) -> Optional[Dict[str, Tuple[int, int]]]:
    """Find X positions of table columns by matching header templates.

    Uses template matching to find column headers and returns their positions.
    The position includes both X coordinate and the template width for calculating
    the cell region to OCR.

    Args:
        extra_columns: Additional column names to detect beyond the standard 3.
            Supported: ["ssn_ein"]. If specified and not found, returns None (hard error).

    Returns:
        Dict with column names and their (x_position, width) tuples, or None if headers not found
    """
    columns = {}

    # Standard column header templates
    header_templates = {
        "client_name": "common/column_header_client_name.png",
        "return_type": "common/column_header_return_type.png",
        "fed_ef_status": "common/column_header_fed_ef_status.png",
    }

    # Add extra columns if requested
    if extra_columns:
        extra_map = {
            "ssn_ein": "common/column_header_ssn_ein.png",
        }
        for col in extra_columns:
            if col in extra_map:
                header_templates[col] = extra_map[col]

    for col_name, template_path in header_templates.items():
        # Find header using template matching (no fallback)
        pos = find_element(template_path, confidence=0.7, fallback_coords=None)

        if pos is None:
            logger.error(f"Column header not found: {col_name} ({template_path})")
            return None

        # Get template width for cell region calculation
        template = load_template(template_path)
        if template is not None:
            template_w = template.shape[1]
        else:
            template_w = 100  # Default width

        columns[col_name] = (pos[0], template_w)
        logger.debug(f"Column '{col_name}' found at x={pos[0]}, width={template_w}")

    logger.info(f"All column headers found: {list(columns.keys())}")
    return columns


def scan_table_row(
    row_index: int,
    row_y: int,
    column_positions: Dict[str, Tuple[int, int]],
    settings: dict
) -> ClientRow:
    """Scan a single table row and extract data via OCR.

    Args:
        row_index: Index of the row (0-based)
        row_y: Y coordinate of the row center
        column_positions: Dict from get_column_positions() (used as fallback)
        settings: Settings dict for column config

    Returns:
        ClientRow with extracted data
    """
    table_settings = settings.get("client_table", {})
    column_config = table_settings.get("columns", {})
    row_height = table_settings.get("row_height", 25)

    # Calculate Y region (top of row)
    region_y = row_y

    # Read each column
    def read_cell(col_name: str) -> str:
        col_cfg = column_config.get(col_name, {})

        # Always use dynamically detected column header position as primary source.
        # The header center_x and template_width tell us where the column actually is,
        # which adapts automatically when TaxAct changes column layout (e.g. after import).
        col_center_x, template_w = column_positions[col_name]
        col_width = col_cfg.get("width", template_w)
        # Align data cell with header LEFT EDGE (center - half template width),
        # with a small left padding to avoid cutting off text at column boundaries.
        cell_x = col_center_x - template_w // 2 - 5

        # Read text from cell region (no preprocessing to match debug_ocr.py behavior;
        # Otsu thresholding can eliminate text with certain colors/contrasts)
        text = read_text_region(cell_x, region_y, col_width, row_height, preprocess=False)
        # Take first non-empty line (OCR sometimes has leading newlines)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return lines[0] if lines else ""

    client_name = read_cell("client_name")
    return_type = normalize_return_type(read_cell("return_type"))
    fed_ef_status = read_cell("fed_ef_status")

    logger.debug(f"Row {row_index}: name='{client_name}', type='{return_type}', status='{fed_ef_status}'")

    return ClientRow(
        row_index=row_index,
        y_position=row_y,
        client_name=client_name,
        return_type=return_type,
        fed_ef_status=fed_ef_status
    )


def _read_single_cell(
    col_name: str,
    row_y: int,
    column_positions: Dict[str, Tuple[int, int]],
    settings: dict
) -> str:
    """Read a single table cell via OCR.

    Extracted from scan_table_row() for use in optimized scanning where
    not all columns need to be read for every row.

    Args:
        col_name: Column name (must exist in column_positions and settings)
        row_y: Y coordinate of the row (top of row)
        column_positions: Dict from get_column_positions()
        settings: Settings dict for column config

    Returns:
        Cell text (first non-empty line), or empty string
    """
    table_settings = settings.get("client_table", {})
    column_config = table_settings.get("columns", {})
    row_height = table_settings.get("row_height", 25)

    col_cfg = column_config.get(col_name, {})
    col_center_x, template_w = column_positions[col_name]
    # Use fixed x/width from settings if available, otherwise derive from template
    if "x" in col_cfg:
        cell_x = col_cfg["x"]
        col_width = col_cfg.get("width", template_w)
    else:
        col_width = col_cfg.get("width", template_w)
        cell_x = col_center_x - template_w // 2 - 5

    text = read_text_region(cell_x, row_y, col_width, row_height, preprocess=False)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return lines[0] if lines else ""


def read_all_rows_from_screenshot(
    screenshot: Image.Image,
    settings: dict,
    start_row: int = 0,
    stop_event: Optional[threading.Event] = None,
) -> List[Tuple[str, str, str, str]]:
    """Read visible table rows from a single PIL screenshot.

    Uses the same proven approach as debug_ocr.py: PIL crop, RGB→GRAY
    conversion, coordinates directly from settings. Skips rows with
    empty client_name without aborting (no break).

    Args:
        screenshot: Full-screen screenshot as PIL Image (RGB)
        settings: Settings dict with client_table.columns config
        start_row: First row index to read (0-based). Use to skip
                   overlap rows after scrolling.

    Returns:
        List of (client_name, ssn_ein, return_type, fed_ef_status) tuples.
        Only rows with non-empty client_name are included.
    """
    table_settings = settings.get("client_table", {})
    columns = table_settings.get("columns", {})
    row_height = table_settings.get("row_height", 25)
    first_data_row_y = table_settings.get("first_data_row_y", 205)
    max_visible_rows = table_settings.get("max_visible_rows", 20)

    col_names = ["client_name", "ssn_ein", "return_type", "fed_ef_status"]
    rows: List[Tuple[str, str, str, str]] = []

    for row_idx in range(start_row, max_visible_rows):
        if stop_event is not None and stop_event.is_set():
            break

        row_y = first_data_row_y + (row_idx * row_height)

        cell_values: List[str] = []
        for col_name in col_names:
            col_cfg = columns.get(col_name, {})
            x = col_cfg.get("x", 0)
            w = col_cfg.get("width", 100)

            # Crop from PIL Image (same approach as debug_ocr.py)
            region = screenshot.crop((x, row_y, x + w, row_y + row_height))

            # RGB → Grayscale → OCR (same as debug_ocr.py)
            region_np = np.array(region)
            region_gray = cv2.cvtColor(region_np, cv2.COLOR_RGB2GRAY)
            region_pil = Image.fromarray(region_gray)
            text = pytesseract.image_to_string(region_pil, lang="eng").strip()

            lines = [line.strip() for line in text.split("\n") if line.strip()]
            cell_values.append(lines[0] if lines else "")

        # Skip rows with empty client_name (no break — continue reading)
        if not cell_values[0]:
            continue

        # Clean OCR artifacts from client name
        client_name = cell_values[0]
        client_name = client_name.lstrip("\u2018\u2019\u201c\u201d")
        client_name = client_name.rstrip(".,_")

        # Fix SSN/EIN missing leading zero: XX-XX-XXXX → 0XX-XX-XXXX
        ssn_ein = cell_values[1]
        if re.match(r"^\d{2}-\d{2}-\d{4}$", ssn_ein):
            ssn_ein = "0" + ssn_ein

        rows.append((client_name, ssn_ein, cell_values[2], cell_values[3]))

    logger.debug(
        f"Read {len(rows)} rows from screenshot (start_row={start_row})"
    )
    return rows


def _scan_visible_clients(
    settings: dict,
    column_positions: Dict[str, Tuple[int, int]],
    processed_clients: Optional[set] = None,
    selected_return_type: str = "1120S",
    csv_records: Optional[list] = None,
    status_updates: Optional[list] = None,
) -> Optional[Tuple[ClientRow, Tuple[int, int], str]]:
    """Scan visible rows and find first matching client.

    Uses optimized read order to minimize OCR calls:
    1. fed_ef_status first — skip immediately if non-empty (1 OCR call)
    2. client_name — detect empty rows / already processed (2 OCR calls)
    Return type is NOT read via OCR — it is set from selected_return_type (user selection).

    When csv_records is provided, uses composite-key (name, id, return_type) for
    skip logic instead of in-memory processed_clients set. Also collects
    auto-status-updates for rows where TaxAct status differs from CSV.

    Args:
        settings: Settings dict
        column_positions: Column positions from get_column_positions()
        processed_clients: Set of already processed client names to skip
        selected_return_type: Return type chosen by user (set in ClientRow)
        csv_records: Optional list of ClientRecord from CSV (for composite-key lookup)
        status_updates: Optional mutable list to collect (name, id, rtype, new_status) tuples

    Returns:
        Tuple of (ClientRow, click_position, last_client_name) or
        (None, None, last_client_name). last_client_name is used for scroll-end detection.
    """
    table_settings = settings.get("client_table", {})
    first_data_row_y = table_settings.get("first_data_row_y", 170)
    row_height = table_settings.get("row_height", 25)
    max_rows = table_settings.get("max_visible_rows", 20)

    if processed_clients is None:
        processed_clients = set()

    # Build skip set from CSV (non-TODO clients)
    has_csv = csv_records is not None
    has_ssn_col = "ssn_ein" in column_positions
    skip_keys = set()
    csv_lookup = {}
    if has_csv:
        for r in csv_records:
            key = (r.client_name, r.client_id, r.return_type)
            if r.status != "TODO":
                skip_keys.add(key)
            csv_lookup[key] = r.status

    last_client_name = ""

    for row_index in range(max_rows):
        row_y = first_data_row_y + (row_index * row_height)

        # Step 1: Read fed_ef_status first (cheapest filter)
        fed_ef_status = _read_single_cell("fed_ef_status", row_y, column_positions, settings)
        if fed_ef_status:
            # Non-empty status → already filed, skip (only 1 OCR call)
            logger.debug(f"Row {row_index}: status='{fed_ef_status}', skipping")
            # Still need client_name for last_client tracking (scroll-end detection)
            client_name = _read_single_cell("client_name", row_y, column_positions, settings)
            if client_name:
                last_client_name = client_name

                # Auto-status-update: compare TaxAct status with CSV
                if has_csv and has_ssn_col and status_updates is not None:
                    ssn_ein = _read_single_cell("ssn_ein", row_y, column_positions, settings)
                    csv_key = (client_name, ssn_ein, selected_return_type)
                    csv_status = csv_lookup.get(csv_key)
                    if csv_status is not None and csv_status != fed_ef_status and csv_status != "TODO":
                        status_updates.append((client_name, ssn_ein, selected_return_type, fed_ef_status))
                        logger.debug(
                            f"Row {row_index}: auto-update {client_name} "
                            f"'{csv_status}' -> '{fed_ef_status}'"
                        )
            continue

        # Step 2: Status is empty → read client_name
        client_name = _read_single_cell("client_name", row_y, column_positions, settings)

        # Empty client_name = end of table data
        if not client_name:
            logger.debug(f"Row {row_index}: empty, stopping scan")
            break

        last_client_name = client_name

        # Read SSN/EIN for CSV composite-key lookup
        ssn_ein = ""
        if has_csv and has_ssn_col:
            ssn_ein = _read_single_cell("ssn_ein", row_y, column_positions, settings)

        # Skip already processed clients
        if has_csv:
            if (client_name, ssn_ein, selected_return_type) in skip_keys:
                logger.debug(f"Row {row_index}: {client_name} not TODO in CSV, skipping")
                continue
        elif client_name in processed_clients:
            logger.debug(f"Row {row_index}: {client_name} already processed, skipping")
            continue

        # Step 3: Read return_type to filter — only process clients matching selected type
        raw_return_type = _read_single_cell("return_type", row_y, column_positions, settings)
        ocr_return_type = normalize_return_type(raw_return_type)

        if ocr_return_type != selected_return_type:
            logger.debug(f"Row {row_index}: {client_name} return type '{ocr_return_type}' != selected '{selected_return_type}', skipping")
            continue

        logger.debug(f"Row {row_index}: name='{client_name}', type='{selected_return_type}', status_empty=True")

        # Use dynamic column position for click target (offset left to avoid "..." menu)
        client_col_x, _ = column_positions["client_name"]
        click_y = row_y + row_height // 2
        click_pos = (client_col_x - 20, click_y)

        row_data = ClientRow(
            row_index=row_index,
            y_position=row_y,
            client_name=client_name,
            return_type=selected_return_type,  # process is determined by GUI, not OCR
            fed_ef_status="",
            client_id=ssn_ein
        )

        logger.info(f"Found client: {client_name} ({selected_return_type}) at row {row_index}")
        return (row_data, click_pos, last_client_name)

    # No match found, return last client name for scroll detection
    return (None, None, last_client_name)


def find_next_client(
    settings: dict,
    selected_return_type: str = "1120S",
    processed_clients: Optional[set] = None,
    csv_records: Optional[list] = None
):
    """Find the next unprocessed client in the Client Manager table.

    Scans visible rows and returns the first client matching:
    - Not in processed_clients set (or not TODO in CSV)
    - Empty Fed EF Status
    Return type is NOT read via OCR — it is set from selected_return_type (user selection).

    If no matching client is visible, scrolls down and re-scans.
    Stops when end of list is detected or max scroll attempts reached.

    When csv_records is provided, also collects auto-status-updates for rows
    where TaxAct status differs from CSV status.

    Args:
        settings: Settings dict from config/settings.json
        selected_return_type: Return type chosen by user in GUI (set in ClientRow)
        processed_clients: Set of client names to skip (already processed)
        csv_records: Optional list of ClientRecord from CSV. When provided,
            uses composite-key lookup instead of processed_clients.

    Returns:
        When csv_records is None (backward-compatible):
            Tuple of (ClientRow, click_position) or None if no client found.
        When csv_records is provided:
            Tuple of (client_result, status_updates) where:
            - client_result is (ClientRow, click_position) or None
            - status_updates is a list of (name, id, rtype, new_status) tuples
    """
    from clickbot import executor

    has_csv = csv_records is not None
    logger.info(
        f"Scanning client table "
        f"(mode={'CSV' if has_csv else 'in-memory'}, "
        f"processed={len(processed_clients or set())} clients)"
    )

    # Get column positions (include SSN/EIN when using CSV)
    if has_csv:
        column_positions = get_column_positions(extra_columns=["ssn_ein"])
    else:
        column_positions = get_column_positions()
    if column_positions is None:
        logger.error("Failed to find column headers - not on Client Manager screen?")
        return (None, []) if has_csv else None

    # Collect auto-status-updates when using CSV
    status_updates = [] if has_csv else None

    # Get loop/scroll settings
    loop_settings = settings.get("loop", {}).get("scroll_in_table", {})
    scroll_x = loop_settings.get("x", 400)
    scroll_y = loop_settings.get("y", 500)
    scroll_amount = loop_settings.get("amount", -300)
    max_scroll_attempts = loop_settings.get("max_attempts", 20)

    last_seen_client = ""

    for scroll_attempt in range(max_scroll_attempts + 1):  # +1 for initial scan without scroll
        # Scan visible rows
        result = _scan_visible_clients(
            settings, column_positions, processed_clients, selected_return_type,
            csv_records=csv_records, status_updates=status_updates
        )

        row_data, click_pos, current_last_client = result

        if row_data is not None:
            # Found a matching client
            client_result = (row_data, click_pos)
            return (client_result, status_updates) if has_csv else client_result

        # No match found in visible rows
        if scroll_attempt == 0:
            # First scan, remember the last client for comparison
            last_seen_client = current_last_client
        else:
            # Check if we've reached the end of the list
            if current_last_client == last_seen_client:
                logger.info("End of client list reached (no new clients after scroll)")
                break
            last_seen_client = current_last_client

        # Scroll down if not at max attempts
        if scroll_attempt < max_scroll_attempts:
            logger.debug(f"Scrolling in client table (attempt {scroll_attempt + 1}/{max_scroll_attempts})")
            executor.scroll(scroll_amount, x=scroll_x, y=scroll_y)
            time.sleep(0.5)  # Wait for scroll to complete

    logger.warning("No unprocessed clients found after scanning entire list")
    return (None, status_updates) if has_csv else None
