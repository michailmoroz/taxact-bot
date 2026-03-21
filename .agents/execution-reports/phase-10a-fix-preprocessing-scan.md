# Execution Report: Phase 10a Fix — Preprocessing Scan Navigation & End-Detection

## Meta
- **Plan file:** `.agents/plans/phase-10a-fix-preprocessing-scan.md`
- **Date:** 2026-03-21
- **Status:** Completed (3 iterations)

## Summary
- **Tasks completed:** 5 / 5 (original) + 2 fix iterations
- **Tests written:** 6 new (26 total in test_preprocessor.py)
- **Tests passing:** 90 / 90 (full unit suite)

## Fix Iterations

### Iteration 1: keyboard → pyautogui (2026-03-21)
- **Change:** Replaced `keyboard.press_and_release()` with `pyautogui.press()` / `pyautogui.hotkey()`
- **Result:** Failed — pyautogui key presses still not received by TaxAct
- **Commit:** `62c22c7`

### Iteration 2: Remove _show_click_splash (2026-03-21)
- **Change:** Removed thread-unsafe `tk.Tk()` splash windows that stole keyboard focus
- **Report:** `.agents/execution-reports/phase-10a-1-fix-splash-focus.md`
- **Result:** Failed — focus was not the issue; pyautogui key events themselves are broken
- **Commit:** `330b383`

### Iteration 3: pyautogui → pydirectinput (2026-03-21)
- **Change:** Replaced `pyautogui.press('down')` and `pyautogui.hotkey('ctrl','home')` with `pydirectinput`
- **Root Cause:** PyAutoGUI uses deprecated `keybd_event()` Win32 API with **scan code = 0** and **no `KEYEVENTF_EXTENDEDKEY` flag**. TaxAct (.NET WinForms/WPF) silently ignores key events without these. `pydirectinput` uses modern `SendInput()` with proper scan codes via `MapVirtualKey` and the extended-key flag.
- **Sources:** [PyAutoGUI #69](https://github.com/asweigart/pyautogui/issues/69), [#115](https://github.com/asweigart/pyautogui/issues/115), [#889](https://github.com/asweigart/pyautogui/issues/889)
- **Result:** Pending manual verification on remote PC

## Files Changed (cumulative, all 3 iterations)

### Modified
| File | Changes |
|------|---------|
| `clickbot/preprocessor.py` | Removed `_show_click_splash` + `import tkinter`; replaced `pyautogui.press('down')` → `pydirectinput.press('down')`; replaced `pyautogui.hotkey('ctrl','home')` → `pydirectinput.keyDown('ctrl') + press('home') + keyUp('ctrl')`; added chunk-scroll handling; added end-of-table detection |
| `config/settings.json` | Added `scroll_reset_row: 8` and `end_repeat_threshold: 4` to preprocessing section |
| `requirements.txt` | Added `pydirectinput>=1.0.4` |
| `tests/unit/test_preprocessor.py` | 6 new tests; updated all 6 preprocess_table tests to mock `pydirectinput` instead of pyautogui for key presses |

## Tests Added
| Test File | Coverage |
|-----------|----------|
| `tests/unit/test_preprocessor.py` | 6 new tests across 3 test classes |

### Test Classes
- `TestPreprocessTableKeyPresses` (2 tests) — verifies pydirectinput.press('down') and pydirectinput Ctrl+Home sequence
- `TestPreprocessTableEndDetection` (3 tests) — threshold detection, below-threshold continuation, empty table
- `TestPreprocessTableChunkScroll` (1 test) — visual_row resets to scroll_reset_row after max

## Validation Results
- [x] Unit tests: 90/90 passed
- [x] No regressions in existing tests

## Key Changes Summary (Final State)

### 1. Key-Press Fix: pyautogui → pydirectinput
```python
# pyautogui (broken — uses keybd_event without scan codes):
pyautogui.hotkey('ctrl', 'home')
pyautogui.press('down')

# pydirectinput (fix — uses SendInput with scan codes + extended key flag):
pydirectinput.keyDown('ctrl')
pydirectinput.press('home')
pydirectinput.keyUp('ctrl')
pydirectinput.press('down')
```

### 2. Chunk-Scroll Handling
```python
if current_visual_row < max_visible_rows - 1:
    current_visual_row += 1
else:
    current_visual_row = scroll_reset_row  # default: 8
```

### 3. End-of-Table Detection
```python
if client_name == prev_client_name:
    repeat_count += 1
    if repeat_count >= end_repeat_threshold:
        break
else:
    repeat_count = 0
prev_client_name = client_name
```

## Manual Verification
- [ ] Preprocessing starten: Pfeiltaste bewegt sichtbar den Fokus in der TaxAct-Tabelle
- [ ] Ctrl+Home scrollt Tabelle nach oben beim Start
- [ ] Sound (play_iteration) kommt für jeden neuen Client
- [ ] Nach ~20 sichtbaren Zeilen: Tabelle scrollt, Bot liest weiter neue Clients
- [ ] Am Tabellenende: Scan stoppt automatisch, "Preprocessing complete!" im Log
- [ ] CSV enthält alle Clients
- [ ] `scroll_reset_row` und `end_repeat_threshold` in settings.json kalibrierbar

## Next Steps
- Deploy to remote PC: `git pull && pip install pydirectinput>=1.0.4`
- Test against real TaxAct
- Calibrate `scroll_reset_row` (default 8) based on observed scroll behavior
- Calibrate `max_visible_rows` (currently 20) in settings.json
