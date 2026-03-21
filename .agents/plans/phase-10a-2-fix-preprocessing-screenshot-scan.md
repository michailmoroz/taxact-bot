# Plan: Fix Preprocessing — Screenshot-Based Page Scan

## User Story

Als Steuerberater möchte ich, dass der Preprocessing-Scan die Client-Tabelle seitenweise per Screenshot liest (wie `debug_ocr.py`), damit OCR-Fehler durch die Zeilen-Selektion (blaues Highlight) vermieden werden und alle Clients korrekt erfasst werden.

## Acceptance Criteria

- [ ] Preprocessing macht **einen Screenshot pro Seite** und liest alle 20 sichtbaren Zeilen daraus
- [ ] Keine Pfeiltaste-Navigation WÄHREND des Lesens (kein Selection-Highlight)
- [ ] Nach dem Lesen: 20x Pfeiltaste-Unten zum Scrollen auf die nächste Seite
- [ ] Dedup filtert die ~9 überlappenden Zeilen zwischen Seiten raus
- [ ] End-Detection: Letzter Client nach Scroll == letzter Client vor Scroll → Stale-Counter +1; bei 3x → fertig
- [ ] Alle bestehenden Unit Tests angepasst und grün
- [ ] E2E: Scan erfasst alle Clients der Tabelle korrekt

## Context

Der aktuelle Preprocessing-Scan liest jede Zeile einzeln, wobei zwischen den Reads die Pfeiltaste-Unten gedrückt wird. Die selektierte Zeile hat in TaxAct ein blaues Highlight, das die OCR-Qualität verschlechtert (Misreads, übersprungene Clients). `debug_ocr.py` zeigt, dass ein einzelner Screenshot ohne Selektion einwandfrei funktioniert. Der Fix stellt den Scan auf seitenweises Lesen um: Screenshot → alle Zeilen lesen → scrollen → wiederholen.

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `clickbot/preprocessor.py` | Hauptmodul — `preprocess_table()` wird umgebaut | 40-211 |
| `clickbot/vision.py` | `_read_single_cell()` liest einzelne Zellen per Screenshot | 793-829 |
| `clickbot/vision.py` | `take_screenshot()` macht Screenshot | 93-112 |
| `clickbot/vision.py` | `read_text_region()` nimmt Screenshot pro Aufruf | 404-439 |
| `debug_ocr.py` | Referenzimplementierung — ein Screenshot, alle Zeilen | 55-101 |
| `tests/unit/test_preprocessor.py` | Unit Tests | 310-548 |
| `config/settings.json` | `client_table` und `preprocessing` Config | 49-76 |

### Patterns to Follow
- `debug_ocr.py:55-101`: Ein Screenshot, Loop über Zeilen, Crop per Region, Grayscale + OCR
- `vision.py:93-112`: `take_screenshot()` für konsistente Screenshot-Funktion
- `vision.py:793-829`: `_read_single_cell()` Spalten-Config-Auswertung (x, width aus settings)

## Dependencies

- **New Packages**: none
- **Affected Modules**: `clickbot/preprocessor.py`, `clickbot/vision.py`, `tests/unit/test_preprocessor.py`
- **Breaking Changes**: Nein — nur internes Refactoring der Scan-Logik

## Tasks

### Task 1: ADD `read_all_rows_from_screenshot()` in `clickbot/vision.py`

- **Action**: ADD
- **Implement**: Neue Funktion, die einen **bereits gemachten** Screenshot (numpy array) und die Spalten-Config entgegennimmt und **alle Zeilen** daraus liest. Gibt `List[Tuple[str, str, str, str]]` zurück (client_name, ssn_ein, return_type, fed_ef_status).
  ```python
  def read_all_rows_from_screenshot(
      screenshot: np.ndarray,
      column_positions: Dict[str, Tuple[int, int]],
      settings: dict,
  ) -> List[Tuple[str, str, str, str]]:
  ```
  - Iteriert über `range(max_visible_rows)` (= 20)
  - Für jede Zeile: Crop-Region berechnen (wie `_read_single_cell` aber aus dem vorhandenen Screenshot statt neuem)
  - OCR pro Zelle: Crop → Grayscale (`cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)`) → `pytesseract.image_to_string()` → erste nicht-leere Zeile
  - Leerer `client_name` → Rest der Zeilen überspringen (Tabelle kürzer als 20)
  - `row_height` ist `float` (43.5) — `int(round(row_y))` für Pixel-Positionen verwenden
- **Pattern**: `debug_ocr.py:74-101` für Crop+OCR aus einem Screenshot; `vision.py:813-829` für Spalten-Config-Auswertung
- **Depends on**: none
- **Validate**: `pytest tests/unit/test_preprocessor.py -v` (nach Task 4)

### Task 2: REFACTOR `preprocess_table()` in `clickbot/preprocessor.py`

- **Action**: REFACTOR
- **Implement**: Kompletter Umbau der Scan-Schleife. Neuer Algorithmus:
  ```
  1. Focus-Click auf Tabelle (pyautogui.click)
  2. Äußere Schleife (max_pages Safety-Limit, z.B. 500):
     a. screenshot = vision.take_screenshot()
     b. rows = vision.read_all_rows_from_screenshot(screenshot, ...)
     c. Für jede Zeile: Dedup via seen_keys Set, Records aufbauen
     d. last_client_on_page = letzter non-empty client_name aus rows
     e. End-Detection:
        - Wenn last_client_on_page == prev_last_client → stale_count += 1
        - Wenn stale_count >= 3 → break (Tabelle-Ende)
        - Sonst stale_count = 0
     f. prev_last_client = last_client_on_page
     g. 20x pydirectinput.press('down') mit arrow_key_delay_s Pause dazwischen
     h. Extra Pause nach dem Scrollen (z.B. 0.5s) damit TaxAct fertig rendert
  3. CSV schreiben (unverändert)
  ```
  - **Entfernen**: `current_visual_row` Tracking, `scroll_reset_row` Logik, `end_repeat_threshold` Logik, per-Zeile `_read_single_cell` Aufrufe
  - **Beibehalten**: Dedup via `seen_keys` Set, `stop_event` Checks, CSV-Schreib-Logik, `sounds.play_iteration()` pro neuem Client
  - Neuer Config-Key `preprocessing.post_scroll_delay_s` (Default 0.5) für die Pause nach dem Scroll-Block
- **Pattern**: Bestehende `preprocess_table()` Struktur (`preprocessor.py:40-211`)
- **Depends on**: Task 1
- **Validate**: `pytest tests/unit/test_preprocessor.py -v` (nach Task 4)

### Task 3: UPDATE `config/settings.json`

- **Action**: UPDATE
- **Implement**:
  - ADD `"post_scroll_delay_s": 0.5` in `preprocessing` Block
  - REMOVE `"scroll_reset_row": 8` (nicht mehr gebraucht)
  - REMOVE `"end_repeat_threshold": 4` (ersetzt durch stale_count=3 Logik)
- **Depends on**: none
- **Validate**: `python -c "import json; json.load(open('config/settings.json'))"`

### Task 4: UPDATE `tests/unit/test_preprocessor.py`

- **Action**: UPDATE
- **Implement**: Tests an neuen Algorithmus anpassen:
  - **Entfernen**: `TestPreprocessTableChunkScroll` Klasse (visual_row Reset gibt es nicht mehr)
  - **Refactor** `TestPreprocessTableKeyPresses`:
    - `test_uses_pydirectinput_press_for_down_arrow` → Verifiziere, dass nach dem Lesen einer Seite 20x `press('down')` aufgerufen wird
  - **Refactor** `TestPreprocessTableEndDetection`:
    - `test_stops_after_threshold_identical_reads` → Umbau: Stale-Detection über 3 identische letzte Clients nach Scroll
    - `test_does_not_stop_for_fewer_repeats` → Anpassen an neue Stale-Logik
    - `test_empty_table_stops_immediately` → Beibehalten (leere erste Seite = sofort fertig)
  - **Neu**: `TestPreprocessTablePageScan`:
    - `test_reads_all_visible_rows_from_single_screenshot` — Verifiziere, dass `take_screenshot()` einmal pro Seite aufgerufen wird (nicht 4x pro Zeile)
    - `test_deduplicates_overlapping_rows_between_pages` — 2 Seiten mit 9 Überlappung, nur Unique in CSV
    - `test_stale_detection_after_three_identical_last_clients` — 3x gleicher letzter Client → Scan stoppt
  - Mocks: `vision.take_screenshot` statt `vision._read_single_cell`, `vision.read_all_rows_from_screenshot` mocken oder Screenshot-Mock verwenden
- **Depends on**: Task 1, Task 2
- **Validate**: `pytest tests/unit/test_preprocessor.py -v`

### Task 5: UPDATE `config/settings.example.json`

- **Action**: UPDATE
- **Implement**: Gleiche Config-Änderungen wie Task 3 (falls diese Datei existiert und preprocessing-Einträge hat)
- **Depends on**: Task 3
- **Validate**: `python -c "import json; json.load(open('config/settings.example.json'))"`

## Testing Requirements

- [ ] `test_reads_all_visible_rows_from_single_screenshot` — Ein Screenshot pro Seite, nicht pro Zelle
- [ ] `test_deduplicates_overlapping_rows_between_pages` — 9 Overlap-Zeilen werden nicht doppelt erfasst
- [ ] `test_stale_detection_after_three_identical_last_clients` — End-Detection funktioniert
- [ ] `test_empty_table_stops_immediately` — Leere Tabelle = sofort fertig
- [ ] `test_uses_pydirectinput_for_page_scroll` — 20x press('down') nach jeder Seite
- [ ] Edge case: Tabelle mit weniger als 20 Clients (nur eine Seite)
- [ ] Edge case: Tabelle mit exakt 20 Clients (eine volle Seite + leere zweite Seite)

**Test Level**: Unit

## Bug Handling

- Bugs durch DIESE Änderungen → sofort fixen
- Vorher existierende Bugs → `.agents/bugs/` dokumentieren, NICHT fixen

## Rollback Strategy

1. `git stash` oder `git checkout .` um alle Änderungen rückgängig zu machen
2. Preprocessing-Funktionalität bleibt über den vorherigen Commit nutzbar

## Manual Verification

- [ ] Bot-GUI "Scan Client Table" starten, Tabelle ist ganz oben
- [ ] Scan erfasst alle Clients (Anzahl vergleichen mit manueller Zählung)
- [ ] Keine Misreads (kein 'â€"' oder ähnlicher Müll)
- [ ] CSV enthält keine Duplikate
- [ ] Scan stoppt am Ende der Tabelle (nicht endlos)
- [ ] Stop-Button unterbricht Scan sofort

## Notes

- `row_height: 43.5` ist nicht ganzzahlig — alle Y-Berechnungen müssen mit `int(round(...))` arbeiten
- Die 20 Pfeiltasten-Drücke zwischen Seiten verwenden `pydirectinput.press('down')` (funktioniert bereits zuverlässig für die Pfeiltaste)
- `normalize_return_type()` wird weiterhin auf den raw OCR-Text angewendet
- `sounds.play_iteration()` wird pro NEUEM Client gespielt (nicht pro Duplikat)

## Confidence Score: 8/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 9 | `debug_ocr.py` ist quasi die Referenzimplementierung |
| **External Knowledge** | 9 | Alles intern, keine neuen Libraries |
| **Risk** | 7 | TaxAct Scroll-Verhalten muss passen (20 Rows = eine Seite) |
| **Dependencies** | 8 | 3 Module betroffen, aber klar abgegrenzt |
| **Clarity** | 9 | Algorithmus vom User klar beschrieben |
| **Testability** | 7 | Unit-Tests mit Mocks, E2E nur manuell gegen TaxAct |

**Overall: 8/10** — Klarer Algorithmus mit bewährtem Pattern (`debug_ocr.py`), einziges Risiko ist das exakte Scroll-Verhalten von TaxAct bei den 20 Arrow-Down-Presses.
