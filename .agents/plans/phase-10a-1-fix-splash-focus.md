# Plan: Phase 10a-1 — Fix Splash-Fokus-Bug im Preprocessing-Scan

## User Story

Als Steuerberater möchte ich, dass der Preprocessing-Scan die TaxAct-Tabelle zuverlässig per Pfeiltaste durchnavigiert, damit alle Clients korrekt erfasst werden.

## Acceptance Criteria

- [ ] `_show_click_splash` ist komplett entfernt (keine `tk.Tk()` im Background-Thread)
- [ ] Pfeiltaste-Unten navigiert sichtbar durch die TaxAct-Tabelle (TaxAct behält Keyboard-Fokus)
- [ ] Ctrl+Home scrollt die Tabelle vor dem Scan korrekt nach oben
- [ ] Bestehende Unit Tests laufen weiterhin (ohne `_show_click_splash`-Mocking)
- [ ] Bot-Loop und GUI bleiben unverändert

## Context

Der Preprocessing-Scan in `preprocessor.py` erstellt `tk.Tk()`-Fenster via `_show_click_splash()` in einem Background-Thread. Tkinter ist nicht thread-safe — das topmost Splash-Fenster stiehlt den Keyboard-Fokus von TaxAct. Dadurch erreichen `pyautogui.press('down')` und `pyautogui.hotkey('ctrl', 'home')` die TaxAct-Tabelle nicht. Lösung: Splash komplett entfernen und den Fokus-Setup-Flow an `bot_controller._scroll_table_to_top()` angleichen.

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `clickbot/preprocessor.py` | Splash-Funktion + Fokus-Setup | L41-65 (splash), L127-141 (focus setup) |
| `clickbot/bot_controller.py` | Referenz: funktionierender Fokus-Flow | L154-164 (`_scroll_table_to_top`) |
| `tests/unit/test_preprocessor.py` | Tests mit `@patch("..._show_click_splash")` | L313, L340, L379, L420, L459, L490 |

### Patterns to Follow
- **`bot_controller.py:154-164`**: Click → sleep(0.2) → Ctrl+Home → sleep(0.3) — kein Splash, kein zweiter Click, funktioniert zuverlässig.
- Alle Tests mocken `_show_click_splash` als separaten Patch — nach Entfernung müssen diese Patches entfernt werden.

## Dependencies

- **New Packages**: none
- **Affected Modules**: `preprocessor.py`, `tests/unit/test_preprocessor.py`
- **Breaking Changes**: Nein — `_show_click_splash` war nur intern verwendet

## Tasks

### Task 1: REMOVE `_show_click_splash` Funktion aus `preprocessor.py`

- **Action**: REMOVE
- **Implement**:
  1. Entferne die gesamte Funktion `_show_click_splash` (Zeilen 41-65)
  2. Entferne `import tkinter as tk` (Zeile 17)
- **Depends on**: none
- **Validate**: `grep -n "tk\.\|_show_click_splash\|import tkinter" clickbot/preprocessor.py` → keine Treffer

### Task 2: UPDATE Fokus-Setup in `preprocess_table`

- **Action**: UPDATE
- **Implement**: Ersetze den bisherigen Fokus-Setup-Block (Zeilen 127-141) mit einem vereinfachten Flow nach dem Muster von `bot_controller.py:154-164`:

  **Vorher:**
  ```python
  # Click on table to give it keyboard focus
  focus_x = preprocessing_settings.get("focus_click_x", 200)
  focus_y = preprocessing_settings.get("focus_click_y", 161)
  _show_click_splash(focus_x, focus_y)
  pyautogui.click(focus_x, focus_y)
  time.sleep(0.3)

  # Scroll to top of table
  pyautogui.hotkey('ctrl', 'home')
  time.sleep(0.3)

  # Re-click to ensure table focus after scroll
  _show_click_splash(focus_x, focus_y)
  pyautogui.click(focus_x, focus_y)
  time.sleep(0.3)
  ```

  **Nachher:**
  ```python
  # Click on table to give it keyboard focus
  focus_x = preprocessing_settings.get("focus_click_x", 200)
  focus_y = preprocessing_settings.get("focus_click_y", 161)
  pyautogui.click(focus_x, focus_y)
  time.sleep(0.3)

  # Scroll to top of table
  pyautogui.hotkey('ctrl', 'home')
  time.sleep(0.5)

  # Re-click to ensure table has keyboard focus after scroll
  pyautogui.click(focus_x, focus_y)
  time.sleep(0.3)
  ```

  **Änderungen:**
  - Beide `_show_click_splash()`-Aufrufe entfernt
  - Delay nach Ctrl+Home von 0.3s auf 0.5s erhöht (TaxAct braucht Zeit zum Scrollen bevor der Re-Click erfolgt)
  - Sonst identisch — der Flow Click → Ctrl+Home → Click bleibt bestehen

- **Pattern**: `bot_controller.py:154-164`
- **Depends on**: Task 1
- **Validate**: `grep -n "_show_click_splash" clickbot/preprocessor.py` → keine Treffer

### Task 3: UPDATE Unit Tests — `_show_click_splash` Patches entfernen

- **Action**: UPDATE
- **Implement**: In `tests/unit/test_preprocessor.py` alle 6 Stellen anpassen, an denen `_show_click_splash` gemockt wird:

  Bei jeder betroffenen Testmethode:
  1. `@patch("clickbot.preprocessor._show_click_splash")` Decorator entfernen
  2. Den zugehörigen `mock_splash` Parameter aus der Methodensignatur entfernen

  Betroffene Tests (6 Stellen):
  - `TestPreprocessTableKeyPresses.test_uses_pyautogui_hotkey_for_ctrl_home` (L313)
  - `TestPreprocessTableKeyPresses.test_uses_pyautogui_press_for_down_arrow` (L340)
  - `TestPreprocessTableEndDetection.test_stops_after_threshold_identical_reads` (L379)
  - `TestPreprocessTableEndDetection.test_does_not_stop_for_fewer_repeats` (L420)
  - `TestPreprocessTableEndDetection.test_empty_table_stops_immediately` (L459)
  - `TestPreprocessTableChunkScroll.test_visual_row_resets_after_max` (L490)

- **Depends on**: Task 1
- **Validate**: `pytest tests/unit/test_preprocessor.py -v`

## Testing Requirements

- [ ] Bestehende 26 Preprocessor-Tests laufen ohne Fehler
- [ ] Kein Test referenziert `_show_click_splash` mehr
- [ ] Gesamte Unit-Suite (90 Tests) ohne Regressionen

**Test Levels**: Unit (bestehend — keine neuen Tests nötig, da nur Entfernung)

## Bug Handling

- Bugs caused by THESE changes → Fix immediately
- Pre-existing bugs → Document in `.agents/bugs/`, do NOT fix
- NEVER modify working code outside the scope of this plan

## Rollback Strategy

1. `git stash` oder `git checkout .` um Änderungen rückgängig zu machen
2. Nur `preprocessor.py` und `test_preprocessor.py` betroffen — kein Risiko für Bot-Loop

## Manual Verification

- [ ] Preprocessing starten: Pfeiltaste bewegt sichtbar den Fokus in der TaxAct-Tabelle
- [ ] Ctrl+Home scrollt die Tabelle zu Beginn nach oben (vor dem Scan-Loop)
- [ ] Nach ~20 sichtbaren Zeilen: Tabelle scrollt weiter, Bot liest neue Clients
- [ ] Am Tabellenende: Scan stoppt automatisch
- [ ] CSV enthält alle Clients

## Notes

- **Root Cause**: `_show_click_splash()` erstellt `tk.Tk()` in einem Background-Thread. Tkinter ist nicht thread-safe. Das topmost Splash-Fenster stiehlt den Keyboard-Fokus von TaxAct, wodurch `pyautogui.press('down')` und `pyautogui.hotkey('ctrl', 'home')` nicht bei TaxAct ankommen.
- **Kein Ersatz nötig**: Der Splash war eine visuelle Debug-Hilfe (roter Punkt). `sounds.play_iteration()` liefert bereits Audio-Feedback pro Client. Log-Messages gehen an die GUI.
- **Delay nach Ctrl+Home**: Von 0.3s auf 0.5s erhöht, damit TaxAct den Scroll vollständig rendert bevor der Re-Focus-Click kommt. Falls nicht ausreichend, kann `preprocessing.ctrl_home_delay_s` in settings.json hinzugefügt werden.

## Confidence Score: 9/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 10 | `bot_controller._scroll_table_to_top` ist das exakte Referenz-Pattern |
| **External Knowledge** | 10 | Nur pyautogui + Tkinter-Thread-Safety — beides trivial |
| **Risk** | 9 | Nur Entfernung von Code, kein neues Verhalten |
| **Dependencies** | 10 | Nur 2 Dateien betroffen, kein Cascade-Effekt |
| **Clarity** | 9 | Root Cause eindeutig identifiziert, Lösung klar |
| **Testability** | 8 | Unit Tests prüfbar, finale Verifikation nur gegen echtes TaxAct |

**Overall: 9/10** — Reine Code-Entfernung mit klarem Root Cause. Kein neues Verhalten, nur Eliminierung der Fokus-störenden Splash-Funktion.
