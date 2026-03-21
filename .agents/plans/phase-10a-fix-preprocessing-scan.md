# Plan: Phase 10a Fix — Preprocessing Scan Navigation & End-Detection

## User Story

Als Steuerberater möchte ich, dass der Preprocessing-Scan die gesamte TaxAct Client-Tabelle zuverlässig durchscrollt und korrekt erkennt, wenn das Tabellenende erreicht ist, damit alle 400+ Clients vollständig erfasst werden.

## Acceptance Criteria

- [ ] Pfeiltaste-Unten navigiert sichtbar durch die TaxAct-Tabelle (Fokus bewegt sich)
- [ ] OCR liest den aktuell fokussierten Client korrekt
- [ ] Chunk-Scroll wird korrekt behandelt (TaxAct springt ~11 Zeilen)
- [ ] Tabellenende wird erkannt: 4 identische Client-Reads hintereinander → Scan beendet
- [ ] Sound (play_iteration) kommt für jeden neuen, einzigartigen Client
- [ ] Bot verarbeitet 400+ Clients ohne hängenzubleiben
- [ ] Bestehende Funktionalität (Bot-Loop, GUI) bleibt unverändert

## Context

Phase 10a (Preprocessing & CSV Export) ist COMPLETE, aber der Scan-Mechanismus in `preprocessor.py` funktioniert nicht korrekt: Die Pfeiltaste hat keinen Effekt in TaxAct (falsches Modul: `keyboard` statt `pyautogui`), die OCR-Position nach Chunk-Scroll ist falsch, und es fehlt eine Abbruchbedingung für das Tabellenende. Dieser Plan fixt diese drei Probleme.

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `clickbot/preprocessor.py` | Scan-Loop, Navigation, End-Detection | L126-202 (gesamter Scan-Flow) |
| `clickbot/bot_controller.py` | Referenz: pyautogui für Ctrl+Home | L154-164 (`_scroll_table_to_top`) |
| `clickbot/process_executor.py` | Referenz: pyautogui für Tasten | L526 (`pyautogui.press(key)`) |
| `config/settings.json` | Preprocessing-Config | L69-74 |

### Patterns to Follow
- **Key-Presses via pyautogui**: `bot_controller.py:162` (`pyautogui.hotkey('ctrl', 'home')`) und `process_executor.py:526` (`pyautogui.press(key)`) — konsistent im gesamten Projekt
- **Scan-Loop**: `preprocessor.py:148-202` — bestehende Struktur wird angepasst, nicht neu geschrieben

### Root Cause Analysis
Der Preprocessor verwendet `keyboard.press_and_release()` für Tastendrücke (Zeile 134, 196), während der gesamte restliche Bot `pyautogui.press()` / `pyautogui.hotkey()` verwendet. Das `keyboard`-Modul generiert offensichtlich Key-Events die TaxAct nicht empfängt. Die Umstellung auf `pyautogui` ist der Fix.

## Dependencies

- **New Packages**: none
- **Affected Modules**: `preprocessor.py`, `settings.json`
- **Breaking Changes**: Nein — nur internes Verhalten des Preprocessing-Scans ändert sich

## Tasks

### Task 1: UPDATE `clickbot/preprocessor.py` — Key-Presses auf pyautogui umstellen

- **Action**: UPDATE
- **Implement**:
  1. Zeile 134: `keyboard.press_and_release('ctrl+home')` → `pyautogui.hotkey('ctrl', 'home')`
  2. Zeile 196: `keyboard.press_and_release('down')` → `pyautogui.press('down')`
  3. Import `keyboard` entfernen (wird nicht mehr benötigt)
- **Pattern**: `bot_controller.py:162` (`pyautogui.hotkey`), `process_executor.py:526` (`pyautogui.press`)
- **Depends on**: none
- **Validate**: `grep -n "keyboard" clickbot/preprocessor.py` → sollte keine Treffer mehr liefern

### Task 2: UPDATE `clickbot/preprocessor.py` — Chunk-Scroll Handling

- **Action**: UPDATE
- **Implement**: In der Scan-Schleife (L148-202) das Tracking von `current_visual_row` anpassen:

  **Aktuell (falsch):**
  ```python
  if current_visual_row < max_visible_rows - 1:
      current_visual_row += 1
  # else: stays at bottom, table auto-scrolls
  ```

  **Neu (korrekt):**
  ```python
  if current_visual_row < max_visible_rows - 1:
      current_visual_row += 1
  else:
      # TaxAct chunk-scrolls: the focused row jumps from the bottom
      # to a middle position (e.g., row 20 becomes row 9).
      # scroll_reset_row defines where the focus lands after scroll.
      current_visual_row = scroll_reset_row
  ```

  `scroll_reset_row` wird aus `settings.json` gelesen:
  ```python
  scroll_reset_row = preprocessing_settings.get("scroll_reset_row", 8)
  ```

  **Logik**: Wenn `current_visual_row` das Maximum erreicht (letzte sichtbare Zeile), bewirkt der nächste Down-Arrow einen Chunk-Scroll. TaxAct verschiebt den Fokus von der letzten Zeile (z.B. Position 19) auf eine mittlere Position (z.B. Position 8). Ab dort inkrementiert `current_visual_row` wieder normal bis zum nächsten Scroll.

- **Pattern**: `preprocessor.py:199-202`
- **Depends on**: Task 1
- **Validate**: `grep -n "scroll_reset_row" clickbot/preprocessor.py` → mindestens 2 Treffer

### Task 3: UPDATE `clickbot/preprocessor.py` — End-of-Table Detection

- **Action**: UPDATE
- **Implement**: Abbruchbedingung in der Scan-Schleife hinzufügen:

  **Vor der Schleife:**
  ```python
  prev_client_name = ""
  repeat_count = 0
  end_repeat_threshold = preprocessing_settings.get("end_repeat_threshold", 4)
  ```

  **In der Schleife, nach dem Lesen von `client_name`:**
  ```python
  # End-of-table detection: N identical reads in a row = table end
  if client_name == prev_client_name:
      repeat_count += 1
      if repeat_count >= end_repeat_threshold:
          logger.info(f"End of table detected: '{client_name}' read {repeat_count + 1} times")
          send_log(f"End of table reached (after {row_num + 1} rows)")
          break
  else:
      repeat_count = 0
  prev_client_name = client_name
  ```

  **Bestehendes `if not client_name: break`** wird beibehalten als zusätzlicher Schutz.

- **Pattern**: Keine direkte Referenz — neue Logik
- **Depends on**: Task 1
- **Validate**: `grep -n "repeat_count" clickbot/preprocessor.py` → mindestens 3 Treffer

### Task 4: UPDATE `config/settings.json` — Neue Preprocessing-Parameter

- **Action**: UPDATE
- **Implement**: `preprocessing`-Abschnitt erweitern:
  ```json
  "preprocessing": {
    "csv_output_dir": "C:/TaxActBot/logs",
    "arrow_key_delay_s": 0.3,
    "focus_click_x": 130,
    "focus_click_y": 220,
    "scroll_reset_row": 8,
    "end_repeat_threshold": 4
  }
  ```
  - `scroll_reset_row`: 0-indexed Position, wo der Fokus nach einem TaxAct-Chunk-Scroll landet (Default: 8 = 9. Zeile). Kalibrierbar per Beobachtung.
  - `end_repeat_threshold`: Anzahl identischer Reads bevor Tabellenende erkannt wird (Default: 4).

- **Pattern**: `settings.json:69-74`
- **Depends on**: none
- **Validate**: `python -c "import json; d=json.load(open('config/settings.json')); p=d['preprocessing']; assert 'scroll_reset_row' in p and 'end_repeat_threshold' in p; print('OK')"`

### Task 5: UPDATE Unit Tests

- **Action**: UPDATE
- **Implement**: Bestehende `preprocessor` Unit Tests erweitern:
  1. **Test End-Detection**: Mock-Scan mit 4 identischen Client-Names → Schleife bricht ab
  2. **Test Chunk-Scroll**: Verifiziere dass `current_visual_row` auf `scroll_reset_row` zurückgesetzt wird nach max
  3. **Test pyautogui statt keyboard**: Verifiziere dass `pyautogui.press('down')` aufgerufen wird (nicht `keyboard`)
- **Depends on**: Task 1-3
- **Validate**: `pytest tests/unit/test_preprocessor.py -v`

## Testing Requirements

- [ ] Unit: End-Detection mit 4 identischen Reads → Scan stoppt
- [ ] Unit: Chunk-Scroll: `current_visual_row` reset auf `scroll_reset_row`
- [ ] Unit: `pyautogui.press('down')` wird aufgerufen (nicht `keyboard.press_and_release`)
- [ ] Unit: `pyautogui.hotkey('ctrl', 'home')` wird aufgerufen (nicht `keyboard`)
- [ ] Edge case: Leere Tabelle (erster Read leer) → sofortiger Stopp

**Test Levels**: Unit

## Bug Handling

- Bugs caused by THESE changes → Fix immediately
- Pre-existing bugs → Document in `.agents/bugs/`, do NOT fix
- NEVER modify working code outside the scope of this plan

## Rollback Strategy

1. `git stash` or `git checkout .` to revert changes
2. Nur `preprocessor.py` und `settings.json` sind betroffen — kein Risiko für Bot-Loop

## Manual Verification

- [ ] Preprocessing starten: Pfeiltaste bewegt sichtbar den Fokus in der TaxAct-Tabelle
- [ ] Sound (play_iteration) kommt für jeden neuen Client
- [ ] Nach ~20 sichtbaren Zeilen: Tabelle scrollt, Bot liest weiter neue Clients
- [ ] Am Tabellenende: Scan stoppt automatisch, "Preprocessing complete!" im Log
- [ ] CSV enthält alle Clients (vergleichen mit manueller Zählung)
- [ ] `scroll_reset_row` und `end_repeat_threshold` in settings.json kalibrierbar

## PRD Update

Phase 10a im PRD ergänzen:
- **Bugfix-Hinweis**: Pfeiltaste-Navigation von `keyboard`-Modul auf `pyautogui` umgestellt (konsistent mit restlichem Bot)
- **Chunk-Scroll Handling**: `scroll_reset_row` konfigurierbar
- **End-of-Table Detection**: `end_repeat_threshold` (Default: 4 identische Reads)

## Notes

- **Root Cause**: `keyboard.press_and_release()` erzeugt Key-Events, die TaxAct nicht verarbeitet. `pyautogui.press()` und `pyautogui.hotkey()` funktionieren im restlichen Bot (bot_controller, process_executor) zuverlässig.
- **scroll_reset_row muss kalibriert werden**: Der Default-Wert 8 basiert auf der Beobachtung "20. wird zum 9." (0-indexed: 8). Falls sich die TaxAct-Grid-Einstellungen ändern, muss dieser Wert in settings.json angepasst werden.
- **`keyboard` Import bleibt in preprocessor.py NICHT erhalten** — wird komplett durch pyautogui ersetzt.
- **max_visible_rows** wird weiterhin aus `settings.json:client_table.max_visible_rows` gelesen (aktuell 27, User hat auf Remote-PC auf 20 geändert). Dieser Wert muss auf dem Remote-PC kalibriert sein.

## Confidence Score: 8/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 10 | `pyautogui.press()` / `pyautogui.hotkey()` bereits überall im Bot verwendet |
| **External Knowledge** | 9 | Nur pyautogui-API, trivial |
| **Risk** | 7 | Chunk-Scroll-Verhalten muss kalibriert werden; `scroll_reset_row` könnte nicht exakt stimmen |
| **Dependencies** | 9 | Nur preprocessor.py + settings.json betroffen |
| **Clarity** | 8 | Anforderungen klar, aber scroll_reset_row muss experimentell bestätigt werden |
| **Testability** | 7 | Key-Press Fix nur manuell gegen echtes TaxAct verifizierbar |

**Overall: 8/10** — Root Cause klar identifiziert (keyboard→pyautogui), Chunk-Scroll-Handling braucht Kalibrierung auf dem Remote-PC.
