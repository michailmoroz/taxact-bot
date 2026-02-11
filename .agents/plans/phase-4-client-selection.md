# Feature: Client Selection from Client Manager Table

The following plan should be complete, but its important that you validate documentation and codebase patterns and task sanity before you start implementing.

## Feature Description

The bot must automatically scan the Client Manager table, identify clients that need processing (empty Fed EF Status + Return Type 1120), and double-click to open them before running the E-File Extension process. Currently, the bot assumes a client is already open - this feature adds the missing client selection step.

## User Story

As a **tax preparer** I want the bot to **automatically find and select the next unprocessed client from the Client Manager table** so that **I don't have to manually select each client before running the automation**.

## Problem Statement

The current implementation (Phase 3) starts the 1120 process assuming a client is already open. The bot cannot:
- Scan the Client Manager table
- Identify clients with empty "Fed EF Status"
- Filter by Return Type (1120 only for now)
- Double-click to open the selected client

## Solution Statement

Add OCR-based table scanning to `vision.py` and update `bot_controller.py` to select a client before executing the process. The bot will:
1. Find column headers via template matching (for X positions)
2. Scan table rows using OCR
3. Find first row where Fed EF Status is empty AND Return Type is "1120"
4. Double-click on the client name to open
5. Then execute the existing 1120.json process

## Feature Metadata

**Feature Type**: Enhancement
**Estimated Complexity**: Medium
**Primary Systems Affected**: vision.py, bot_controller.py
**Dependencies**: OpenCV (existing), pytesseract (existing)

---

## CONTEXT REFERENCES

### Relevant Codebase Files (MUST READ BEFORE IMPLEMENTING!)

| File | Lines | Why |
|------|-------|-----|
| `clickbot/vision.py` | Full | Pattern for template matching, OCR functions |
| `clickbot/bot_controller.py` | 121-155 | Where client selection must be added (before process execution) |
| `clickbot/process_executor.py` | 69-140 | How process execution works |
| `clickbot/executor.py` | Full | Double-click function |
| `config/settings.json` | Full | Vision settings, OCR config |

### New Files to Create

| File | Purpose |
|------|---------|
| None | All changes in existing files |

### Files to Modify

| File | Changes |
|------|---------|
| `clickbot/vision.py` | Add `scan_client_table()`, `find_next_client()` functions |
| `clickbot/bot_controller.py` | Add client selection before process execution |
| `config/settings.json` | Add `client_table` section with row height, column offsets |

### Screenshots Available

| Screenshot | Purpose |
|------------|---------|
| `common/client_manager_table.png` | Reference for table structure |
| `common/column_header_client_name.png` | Find Client column X position |
| `common/column_header_return_type.png` | Find Return Type column X position |
| `common/column_header_fed_ef_status.png` | Find Fed EF Status column X position |

### Patterns to Follow

**Template Matching Pattern (vision.py:119-190):**
```python
def find_element(
    image_path: str,
    confidence: Optional[float] = None,
    fallback_coords: Optional[Tuple[int, int]] = None,
    region: Optional[Tuple[int, int, int, int]] = None
) -> Optional[Tuple[int, int]]:
    # Load template, take screenshot, cv2.matchTemplate
    # Return center coordinates
```

**OCR Pattern (vision.py:276-316):**
```python
def read_text_region(
    x: int, y: int, width: int, height: int,
    preprocess: bool = True
) -> str:
    screenshot = take_screenshot(region=(x, y, width, height))
    # Preprocess, OCR, return text
```

**Logging Pattern:**
```python
logger.info(f"Found client: {client_name} at row {row_index}")
logger.debug(f"OCR result for region ({x}, {y}): '{text}'")
logger.warning(f"No unprocessed clients found")
```

**Config Pattern (settings.json):**
```json
{
  "vision": {
    "confidence_threshold": 0.8,
    "retry_count": 3
  }
}
```

---

## IMPLEMENTATION PLAN

### Phase 1: Configuration

Add client table settings to config for easy adjustment of row heights and column offsets.

### Phase 2: Vision Module Enhancement

Add functions to scan the client table and find the next unprocessed client.

### Phase 3: Bot Controller Integration

Update bot_controller.py to select a client before running the process.

### Phase 4: Testing & Validation

Manual testing with TaxAct to verify client selection works.

---

## STEP-BY-STEP TASKS

### Task 1: UPDATE `config/settings.json`

Add client table configuration section.

- **IMPLEMENT**: Add `client_table` section with row height, table region, and column settings
- **PATTERN**: Follow existing `vision` section structure
- **VALIDATE**: `python -c "import json; json.load(open('config/settings.json'))"`

```json
{
  "client_table": {
    "row_height": 25,
    "table_start_y_offset": 30,
    "max_visible_rows": 20,
    "columns": {
      "client_name": { "width": 200 },
      "return_type": { "width": 80 },
      "fed_ef_status": { "width": 100 }
    }
  }
}
```

---

### Task 2: UPDATE `clickbot/vision.py` - Add `get_column_positions()`

Find X positions of table columns using template matching.

- **IMPLEMENT**: Function that finds column headers and returns their X positions
- **PATTERN**: Use existing `find_element()` pattern
- **IMPORTS**: None (use existing imports)
- **VALIDATE**: `python -m py_compile clickbot/vision.py`

```python
def get_column_positions() -> Optional[Dict[str, int]]:
    """Find X positions of table columns by matching header templates.

    Returns:
        Dict with column names and their X positions, or None if headers not found
    """
```

---

### Task 3: UPDATE `clickbot/vision.py` - Add `scan_table_row()`

Read a single table row using OCR.

- **IMPLEMENT**: Function that reads client name, return type, and fed ef status from a row
- **PATTERN**: Use existing `read_text_region()` pattern
- **IMPORTS**: None (use existing imports)
- **VALIDATE**: `python -m py_compile clickbot/vision.py`

```python
@dataclass
class ClientRow:
    """Data from a single client table row."""
    row_index: int
    y_position: int
    client_name: str
    return_type: str
    fed_ef_status: str

def scan_table_row(
    row_index: int,
    row_y: int,
    column_positions: Dict[str, int],
    settings: dict
) -> ClientRow:
    """Scan a single table row and extract data via OCR."""
```

---

### Task 4: UPDATE `clickbot/vision.py` - Add `find_next_client()`

Main function to find the next unprocessed client.

- **IMPLEMENT**: Scan visible rows, find first with empty Fed EF Status and Return Type 1120
- **PATTERN**: Combine `get_column_positions()` and `scan_table_row()`
- **IMPORTS**: Add `from dataclasses import dataclass` if not present
- **VALIDATE**: `python -m py_compile clickbot/vision.py`

```python
def find_next_client(
    settings: dict,
    target_return_type: str = "1120"
) -> Optional[Tuple[ClientRow, Tuple[int, int]]]:
    """Find the next unprocessed client in the table.

    Args:
        settings: Settings dict
        target_return_type: Return type to filter for (default "1120")

    Returns:
        Tuple of (ClientRow, click_position) or None if no client found
    """
```

---

### Task 5: UPDATE `clickbot/bot_controller.py` - Add client selection

Integrate client selection into the bot run loop.

- **IMPLEMENT**: Call `find_next_client()` before `executor.execute()`, double-click to open
- **PATTERN**: Follow existing message queue pattern for status updates
- **IMPORTS**: Add `from clickbot import vision` and `from clickbot import executor`
- **GOTCHA**: Must handle case where no clients found (return early with message)
- **VALIDATE**: `python -m py_compile clickbot/bot_controller.py`

Changes to `_run()` method:
```python
def _run(self) -> None:
    # 1. Find next client
    self.message_queue.put(StatusMessage("status", "Scanning client table..."))
    result = vision.find_next_client(self.settings, "1120")

    if result is None:
        self.message_queue.put(StatusMessage("complete", "No unprocessed clients found"))
        sounds.play_complete()
        self.state = BotState.IDLE
        return

    client_row, click_pos = result
    self.message_queue.put(StatusMessage("log", f"Selected: {client_row.client_name} ({client_row.return_type})"))

    # 2. Double-click to open client
    executor.double_click(click_pos[0], click_pos[1], wait=2.0)

    # 3. Execute process (existing code)
    ...
```

---

### Task 6: CREATE `tests/manual/test_client_selection.py`

Manual test script for client selection.

- **IMPLEMENT**: Test script that runs client selection without full process
- **PATTERN**: Follow `tests/manual/test_phase3.py` structure
- **VALIDATE**: `python -m tests.manual.test_client_selection`

---

## TESTING STRATEGY

### Unit Tests

Not applicable - OCR/vision functions require real screen content.

### Integration Tests

Manual testing with TaxAct running:
1. Open TaxAct Client Manager with mix of 1120/1120S clients
2. Ensure some clients have empty Fed EF Status
3. Run test script to verify:
   - Column headers are found
   - Table rows are scanned correctly
   - Correct client is selected (1120 with empty status)

### Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| No clients with empty Fed EF Status | Bot shows "No unprocessed clients found" |
| Only 1120S clients with empty status | Bot skips them (1120 only) |
| Column headers not found | Bot shows error, stops |
| OCR reads incorrect text | Fallback: try next row |

---

## VALIDATION COMMANDS

### Level 1: Syntax Check

```bash
python -m py_compile clickbot/vision.py
python -m py_compile clickbot/bot_controller.py
python -c "import json; json.load(open('config/settings.json'))"
```

### Level 2: Import Check

```bash
python -c "from clickbot.vision import find_next_client, get_column_positions, scan_table_row"
```

### Level 3: Manual Test Script

```bash
python -m tests.manual.test_client_selection
```

### Level 4: Full E2E Test (with TaxAct)

```bash
python -m clickbot.gui
```

Prerequisites:
- TaxAct 2025 open on primary monitor
- Client Manager visible
- At least one 1120 client with empty Fed EF Status

---

## ACCEPTANCE CRITERIA

- [x] `config/settings.json` has `client_table` section
- [ ] `vision.py` has `get_column_positions()` function
- [ ] `vision.py` has `scan_table_row()` function
- [ ] `vision.py` has `find_next_client()` function
- [ ] `bot_controller.py` selects client before process execution
- [ ] Bot correctly identifies clients with empty Fed EF Status
- [ ] Bot correctly filters by Return Type 1120
- [ ] Bot double-clicks to open selected client
- [ ] Bot shows "No unprocessed clients" when table is empty
- [ ] All syntax checks pass

---

## COMPLETION CHECKLIST

- [ ] Task 1: settings.json updated
- [ ] Task 2: get_column_positions() implemented
- [ ] Task 3: scan_table_row() implemented
- [ ] Task 4: find_next_client() implemented
- [ ] Task 5: bot_controller.py updated
- [ ] Task 6: Test script created
- [ ] All validation commands pass
- [ ] Manual testing with TaxAct confirms functionality

---

## NOTES

### Table Structure (from screenshot analysis)

| Column | Approximate X | Width |
|--------|--------------|-------|
| Client | 20 | 200 |
| SSN/EIN | 220 | 100 |
| Return Type | 320 | 80 |
| Return Status | 400 | 80 |
| Fed EF Status | 480 | 100 |

Row height: ~25 pixels
Header row Y: ~145 pixels
First data row Y: ~170 pixels

### OCR Considerations

- Fed EF Status values: empty string, "Ext: Accepted", "Ext: Rejected", "Imported" (in Return Status column, not Fed EF)
- Return Type values: "1120", "1120S"
- Client names: ALL CAPS typically

### Design Decisions

1. **Scan visible rows only**: Don't scroll yet - Phase 6 will add scrolling
2. **Template matching for headers**: More reliable than fixed coordinates
3. **OCR for cell content**: Headers give X position, then read cell at that X
4. **Stop on first match**: Don't scan entire table, select first valid client

### Future Enhancements (Out of Scope)

- Scroll through table to find more clients (Phase 6)
- Support for 1120S return type (Phase 5)
- Client tracking to avoid re-processing (Phase 6)
