# Execution Report: Phase 10a-1 — Fix Preprocessing-Scan Key Input

## Meta
- **Plan file:** `.agents/plans/phase-10a-1-fix-splash-focus.md`
- **Date:** 2026-03-21
- **Status:** Completed (5 iterations)

## Summary
- **Tasks completed:** 5 iterations of key input fixes
- **Tests passing:** 90 / 90 (full unit suite)

## Fix Iterations

### Iteration 1: keyboard → pyautogui (2026-03-21)
- `keyboard.press_and_release()` → `pyautogui.press()` / `pyautogui.hotkey()`
- **Result:** ❌ pyautogui uses `keybd_event()` without scan codes or extended key flag
- **Commit:** `62c22c7`

### Iteration 2: Remove _show_click_splash (2026-03-21)
- Removed thread-unsafe `tk.Tk()` splash windows
- **Result:** ❌ Focus wasn't the root cause for key input failure
- **Commit:** `330b383`

### Iteration 3: pyautogui → pydirectinput for arrow keys (2026-03-21)
- `pyautogui.press('down')` → `pydirectinput.press('down')`
- Also tried `pydirectinput` for Ctrl+Home
- **Result:** ✅ Arrow down works! ❌ Ctrl+Home still fails (pydirectinput doesn't set extended flag for Home)
- **Commit:** `164e106`

### Iteration 4: Revert Ctrl+Home to pyautogui (2026-03-21)
- `pydirectinput Ctrl+Home` → `pyautogui.hotkey('ctrl', 'home')`
- **Result:** ❌ pyautogui also can't send Home with extended key flag
- **Commit:** `5520795`

### Iteration 5: Atomic ctypes SendInput for Ctrl+Home (2026-03-21)
- Created `clickbot/winkeys.py` — atomic `SendInput()` with correct scan codes + `KEYEVENTF_EXTENDEDKEY`
- `pyautogui.hotkey('ctrl', 'home')` → `winkeys.send_ctrl_home()`
- **Result:** ⏳ Pending manual verification on remote PC

## Files Changed (cumulative)

### Created
| File | Purpose |
|------|---------|
| `clickbot/winkeys.py` | Atomic Ctrl+Home via ctypes `SendInput()` with proper scan codes and `KEYEVENTF_EXTENDEDKEY` |

### Modified
| File | Changes |
|------|---------|
| `clickbot/preprocessor.py` | Removed `_show_click_splash` + `import tkinter`; arrow down via `pydirectinput.press('down')`; Ctrl+Home via `winkeys.send_ctrl_home()` |
| `clickbot.spec` | Added `pydirectinput` and `clickbot.winkeys` to `hiddenimports` |
| `requirements.txt` | Added `pydirectinput>=1.0.4` |
| `tests/unit/test_preprocessor.py` | Updated 6 tests: mock `winkeys` + `pydirectinput`, removed splash patches |

## Final Key Input Strategy

| Action | Module | Why |
|--------|--------|-----|
| Mouse click/scroll | `pyautogui` | Mouse events work fine |
| Arrow Down | `pydirectinput` | SendInput with extended key flag for arrow keys |
| Ctrl+Home | `winkeys` (ctypes) | Atomic SendInput with extended key flag for Home |

## Validation Results
- [x] Unit tests: 90/90 passed
- [x] No regressions

## Root Cause Summary

**Arrow keys:** PyAutoGUI uses deprecated `keybd_event()` with scan_code=0 and no `KEYEVENTF_EXTENDEDKEY`. TaxAct (.NET) ignores these. Fix: `pydirectinput` which uses `SendInput()` with scan codes and extended flag for arrows.

**Ctrl+Home:** Neither pyautogui nor pydirectinput work:
- pyautogui: no scan code, no extended flag
- pydirectinput: hardcodes `KEYEVENTF_EXTENDEDKEY` only for `['up','left','down','right']`, not Home. Also sends 3 separate `SendInput()` calls with 100ms pause each (non-atomic).
- Fix: `winkeys.send_ctrl_home()` sends all 4 key events in ONE `SendInput()` call with `KEYEVENTF_SCANCODE | KEYEVENTF_EXTENDEDKEY` for Home.

## Manual Verification
- [x] Pfeiltaste-Unten navigiert sichtbar durch die TaxAct-Tabelle ✅
- [ ] Ctrl+Home scrollt die Tabelle zu Beginn nach oben
- [ ] Nach ~20 sichtbaren Zeilen: Tabelle scrollt weiter, Bot liest neue Clients
- [ ] Am Tabellenende: Scan stoppt automatisch
- [ ] CSV enthält alle Clients

## Next Steps
- Deploy to remote PC: `git pull && scripts\build.bat`
- Test Ctrl+Home against real TaxAct
