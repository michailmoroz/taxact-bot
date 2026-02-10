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
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

import cv2
import numpy as np
import pyautogui
import pytesseract
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
    max_val = 0

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


def get_column_positions() -> Optional[Dict[str, Tuple[int, int]]]:
    """Find X positions of table columns by matching header templates.

    Uses template matching to find column headers and returns their positions.
    The position includes both X coordinate and the template width for calculating
    the cell region to OCR.

    Returns:
        Dict with column names and their (x_position, width) tuples, or None if headers not found
    """
    columns = {}

    # Column header templates to find
    header_templates = {
        "client_name": "common/column_header_client_name.png",
        "return_type": "common/column_header_return_type.png",
        "fed_ef_status": "common/column_header_fed_ef_status.png",
    }

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
        col_width = col_cfg.get("width", 100)

        # Use explicit X from config if available, otherwise use template matching result
        if "x" in col_cfg:
            cell_x = col_cfg["x"]
        else:
            # Fallback to template matching position
            col_x, _ = column_positions[col_name]
            cell_x = col_x - col_width // 2

        # Read text from cell region
        text = read_text_region(cell_x, region_y, col_width, row_height, preprocess=True)
        return text.strip()

    client_name = read_cell("client_name")
    return_type = read_cell("return_type")
    fed_ef_status = read_cell("fed_ef_status")

    logger.debug(f"Row {row_index}: name='{client_name}', type='{return_type}', status='{fed_ef_status}'")

    return ClientRow(
        row_index=row_index,
        y_position=row_y,
        client_name=client_name,
        return_type=return_type,
        fed_ef_status=fed_ef_status
    )


def find_next_client(
    settings: dict,
    target_return_type: str = "1120"
) -> Optional[Tuple[ClientRow, Tuple[int, int]]]:
    """Find the next unprocessed client in the Client Manager table.

    Scans visible rows and returns the first client matching:
    - Empty Fed EF Status
    - Return Type matches target_return_type

    Args:
        settings: Settings dict from config/settings.json
        target_return_type: Return type to filter for (default "1120")

    Returns:
        Tuple of (ClientRow, click_position) or None if no client found.
        click_position is the (x, y) for double-clicking the client name.
    """
    logger.info(f"Scanning client table for return type: {target_return_type}")

    # Get column positions
    column_positions = get_column_positions()
    if column_positions is None:
        logger.error("Failed to find column headers - not on Client Manager screen?")
        return None

    # Get table settings
    table_settings = settings.get("client_table", {})
    first_data_row_y = table_settings.get("first_data_row_y", 170)
    row_height = table_settings.get("row_height", 25)
    max_rows = table_settings.get("max_visible_rows", 20)

    # Scan each visible row
    for row_index in range(max_rows):
        row_y = first_data_row_y + (row_index * row_height)

        # Read row data
        row_data = scan_table_row(row_index, row_y, column_positions, settings)

        # Skip empty rows (no client name)
        if not row_data.client_name:
            logger.debug(f"Row {row_index}: empty, stopping scan")
            break

        # Check if this client matches our criteria
        # Fed EF Status must be empty
        is_status_empty = len(row_data.fed_ef_status) == 0

        # Return Type must match (handle OCR variations like "1120" vs "11205")
        type_matches = target_return_type in row_data.return_type

        logger.debug(f"Row {row_index}: status_empty={is_status_empty}, type_matches={type_matches}")

        if is_status_empty and type_matches:
            # Found a match! Calculate click position (client name column)
            client_col_cfg = table_settings.get("columns", {}).get("client_name", {})
            if "x" in client_col_cfg:
                # Use config x + half width for center of cell
                client_col_x = client_col_cfg["x"] + client_col_cfg.get("width", 200) // 2
            else:
                client_col_x, _ = column_positions["client_name"]
            click_pos = (client_col_x, row_y)

            logger.info(f"Found client: {row_data.client_name} ({row_data.return_type}) at row {row_index}")
            return (row_data, click_pos)

    logger.warning(f"No unprocessed clients found with return type {target_return_type}")
    return None
