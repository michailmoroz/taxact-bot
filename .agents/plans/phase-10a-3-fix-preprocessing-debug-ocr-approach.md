# Plan: Fix Preprocessing — debug_ocr-Ansatz übernehmen

## User Story

Als Steuerberater möchte ich, dass der Preprocessing-Scan die gleiche bewährte OCR-Methode wie `debug_ocr.py` verwendet und nach dem Scrollen nur die tatsächlich neuen Clients liest, damit alle Clients zuverlässig erkannt werden und keine übersprungen werden.

## Acceptance Criteria

- [ ] `read_all_rows_from_screenshot()` verwendet exakt den `debug_ocr.py`-Ansatz (PIL direkt, RGB→GRAY, Koordinaten aus Settings)
- [ ] Kein `break` bei leerem `client_name` — alle Rows werden durchgelesen
- [ ] Seite 1: Rows 0–19 lesen (alle 20)
- [ ] Ab Seite 2: Nur Rows 9–19 lesen (die 11 neuen Clients), Rows 0–8 überspringen
- [ ] Dedup via `seen_keys` bleibt als Safety-Net erhalten
- [ ] `debug_ocr.py` `NUM_ROWS` von 27 auf 20 geändert
- [ ] Alle Unit Tests angepasst und grün
- [ ] End-Detection und Scroll-Logik unverändert

## Context

Der aktuelle `read_all_rows_from_screenshot()` in `vision.py` hat zwei Probleme: (1) ein `break` bei leerem `client_name` überspringt alle nachfolgenden Rows auf einer Seite, (2) eine unnötig komplexe Konvertierungskette (RGB→BGR→GRAY statt RGB→GRAY). `debug_ocr.py` verwendet einen einfacheren, bewiesenermaßen funktionierenden Ansatz. Zusätzlich liest der Code nach jedem Scroll alle 20 Rows, obwohl nur die letzten 11 neu sind (9 Overlap von der vorherigen Seite).

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `debug_ocr.py` | Referenzimplementierung — PIL direkt, RGB→GRAY, funktioniert perfekt | 74-99 |
| `clickbot/vision.py` | `read_all_rows_from_screenshot()` — wird refactored | 832-899 |
| `clickbot/vision.py` | `take_screenshot()` — macht RGB→BGR Konvertierung (wird nicht mehr gebraucht) | 93-112 |
| `clickbot/preprocessor.py` | `preprocess_table()` — ruft `read_all_rows_from_screenshot()` auf, bekommt `start_row` Parameter | 105-183 |
| `tests/unit/test_preprocessor.py` | Tests für `preprocess_table()` — werden angepasst | 300-551 |
| `config/settings.json` | `client_table` Konfiguration — neuer `overlap_rows` Key | 49-60 |

### Patterns to Follow
- `debug_ocr.py:55`: `pyautogui.screenshot()` → PIL Image (RGB)
- `debug_ocr.py:86`: `screenshot.crop((x1, y1, x2, y2))` → PIL crop
- `debug_ocr.py:92-94`: `np.array(region)` → `cv2.cvtColor(RGB2GRAY)` → `Image.fromarray(gray)`
- `debug_ocr.py:95`: `pytesseract.image_to_string(region_pil, lang="eng")`
- `debug_ocr.py:74-76`: Koordinaten direkt aus `settings["client_table"]["columns"]`

## Dependencies

- **New Packages**: none
- **Affected Modules**: `clickbot/vision.py`, `clickbot/preprocessor.py`, `debug_ocr.py`, `config/settings.json`, `tests/unit/test_preprocessor.py`
- **Breaking Changes**: Nein — `read_all_rows_from_screenshot()` bekommt neuen optionalen Parameter `start_row`, Default 0 = bisheriges Verhalten

## Tasks

### Task 1: REFACTOR `read_all_rows_from_screenshot()` in `clickbot/vision.py`

- **Action**: REFACTOR
- **Implement**: Die Funktion komplett auf den `debug_ocr.py`-Ansatz umstellen:
  1. **Signatur erweitern**: Neuer Parameter `start_row: int = 0` — ab welcher Row gelesen wird
  2. **Screenshot als PIL Image akzeptieren** statt BGR numpy array. Typ-Annotation: `screenshot: Image.Image`
  3. **Koordinaten direkt aus `settings["client_table"]["columns"]`** lesen — kein `column_positions`-Parameter mehr nötig. Parameter entfernen.
  4. **Neue Signatur**:
     ```python
     def read_all_rows_from_screenshot(
         screenshot: Image.Image,
         settings: dict,
         start_row: int = 0,
     ) -> List[Tuple[str, str, str, str]]:
     ```
  5. **Crop via PIL**: `screenshot.crop((x1, y1, x2, y2))` wie `debug_ocr.py:86`
  6. **Grayscale via RGB→GRAY**: `cv2.cvtColor(np.array(region), cv2.COLOR_RGB2GRAY)` wie `debug_ocr.py:92-93`
  7. **Kein `break` bei leerem client_name** — stattdessen `continue` verwenden. Row wird einfach übersprungen. Kein frühzeitiger Abbruch.
  8. **Loop von `start_row` bis `max_visible_rows`**: `for row_idx in range(start_row, max_visible_rows)`
  9. **Row Y Berechnung wie debug_ocr.py**: `row_y = first_data_row_y + (row_idx * row_height)` — float, PIL `crop()` truncated automatisch
  10. **Rückgabe**: Liste von `(client_name, ssn_ein, return_type, fed_ef_status)` Tuples — nur Rows mit nicht-leerem `client_name`
- **Pattern**: `debug_ocr.py:74-99`
- **Depends on**: none
- **Validate**: `pytest tests/unit/test_preprocessor.py -v`

### Task 2: UPDATE `preprocess_table()` in `clickbot/preprocessor.py`

- **Action**: UPDATE
- **Implement**:
  1. **Screenshot als PIL Image**: `pyautogui.screenshot()` direkt verwenden statt `vision.take_screenshot()` (das macht unnötig RGB→BGR). Import `pyautogui` ist bereits vorhanden.
  2. **`read_all_rows_from_screenshot()` Aufruf anpassen**: Kein `column_positions` Parameter mehr, dafür `start_row`:
     - Seite 0 (erste Seite): `start_row=0` → alle 20 Rows
     - Ab Seite 1: `start_row=overlap_rows` → nur die neuen Rows (ab Row 9)
  3. **`overlap_rows` aus Settings lesen**: `preprocessing.overlap_rows` (Default: 9)
  4. **`column_positions`-Aufruf (`vision.get_column_positions`) entfernen** — wird nicht mehr benötigt, da Koordinaten direkt aus Settings gelesen werden. Damit entfällt auch die Abhängigkeit von Template-Matching für den Preprocessing-Scan.
  5. **`vision.take_screenshot()` Aufruf ersetzen** durch `pyautogui.screenshot()` (PIL Image)
  6. **Restliche Logik unverändert**: Dedup, Stale-Detection, Scroll, CSV-Schreiben
- **Pattern**: Bestehende `preprocess_table()` Struktur (`preprocessor.py:105-183`)
- **Depends on**: Task 1
- **Validate**: `pytest tests/unit/test_preprocessor.py -v`

### Task 3: ADD `overlap_rows` in `config/settings.json`

- **Action**: UPDATE
- **Implement**: Im `preprocessing`-Block hinzufügen:
  ```json
  "overlap_rows": 9
  ```
- **Depends on**: none
- **Validate**: `python -c "import json; json.load(open('config/settings.json'))"`

### Task 4: UPDATE `debug_ocr.py`

- **Action**: UPDATE
- **Implement**: `NUM_ROWS = 27` → `NUM_ROWS = 20` (Zeile 40)
- **Depends on**: none
- **Validate**: Datei ist syntaktisch korrekt

### Task 5: UPDATE `tests/unit/test_preprocessor.py`

- **Action**: UPDATE
- **Implement**: Tests an die neue API anpassen:
  1. **`_make_page_reader()` anpassen**: Nimmt jetzt `(screenshot, settings, start_row=0)` statt `(screenshot, column_positions, settings)`. Muss `start_row` berücksichtigen und die entsprechenden Rows zurückgeben.
  2. **Mock-Anpassung**: `mock_vision.read_all_rows_from_screenshot` statt `mock_vision.take_screenshot` + `mock_vision.read_all_rows_from_screenshot` → jetzt `mock_pyautogui.screenshot` + `mock_vision.read_all_rows_from_screenshot`
  3. **`MOCK_COLUMN_POSITIONS` entfernen** — wird nicht mehr verwendet
  4. **`mock_vision.get_column_positions` Mocks entfernen** — Funktion wird nicht mehr aufgerufen
  5. **`TestPreprocessTablePageScan` anpassen**:
     - `test_reads_all_rows_from_single_screenshot`: Verifiziere `pyautogui.screenshot()` statt `vision.take_screenshot()`
     - `test_deduplicates_overlapping_rows_between_pages`: Beibehalten, Mock anpassen
  6. **Neuer Test: `test_second_page_starts_from_overlap_row`**: Verifiziere, dass `read_all_rows_from_screenshot` auf Seite 2+ mit `start_row=9` aufgerufen wird
  7. **`TestPreprocessTableKeyPresses`**: Mock-Anpassung (kein `column_positions`)
  8. **`TestPreprocessTableEndDetection`**: Alle Tests anpassen (kein `column_positions`, `pyautogui.screenshot` statt `vision.take_screenshot`)
  9. **`base_settings` Fixture**: `"overlap_rows": 2` hinzufügen (für Test-Zwecke kleiner als 9)
- **Depends on**: Task 1, Task 2
- **Validate**: `pytest tests/unit/test_preprocessor.py -v`

### Task 6: UPDATE `config/settings.example.json`

- **Action**: UPDATE
- **Implement**: `"overlap_rows": 9` im `preprocessing`-Block hinzufügen (wie Task 3)
- **Depends on**: Task 3
- **Validate**: `python -c "import json; json.load(open('config/settings.example.json'))"`

## Testing Requirements

- [ ] `test_reads_all_rows_from_single_screenshot` — Ein Screenshot (PIL) pro Seite
- [ ] `test_deduplicates_overlapping_rows_between_pages` — Dedup funktioniert weiterhin
- [ ] `test_second_page_starts_from_overlap_row` — Seite 2+ liest ab `start_row=overlap_rows`
- [ ] `test_first_page_reads_all_rows` — Seite 1 liest ab `start_row=0`
- [ ] `test_stale_detection_after_three_identical_last_clients` — End-Detection unverändert
- [ ] `test_empty_table_stops_immediately` — Leere Tabelle stoppt sofort
- [ ] `test_presses_down_arrow_max_visible_rows_times_per_page` — Scroll-Verhalten unverändert
- [ ] Edge case: Tabelle mit weniger als 20 Clients (nur eine Seite, kein Scroll)
- [ ] Edge case: Row mit leerem client_name in der Mitte wird übersprungen (kein Break)

**Test Level**: Unit

## Bug Handling

- Bugs durch DIESE Änderungen → sofort fixen
- Vorher existierende Bugs → `.agents/bugs/` dokumentieren, NICHT fixen
- NEVER modify working code outside the scope of this plan

## Rollback Strategy

1. `git stash` oder `git checkout .` um alle Änderungen rückgängig zu machen
2. Preprocessing-Funktionalität bleibt über den vorherigen Commit nutzbar

## Manual Verification

- [ ] Bot-GUI "Scan Client Table" starten, Tabelle ganz oben
- [ ] Scan erfasst ALLE Clients (Anzahl vergleichen mit manueller Zählung)
- [ ] Client-Namen korrekt gelesen (Vergleich mit TaxAct)
- [ ] Ab Seite 2: Nur 11 Sound-Beeps pro Seite (nicht 20)
- [ ] CSV enthält keine Duplikate
- [ ] CSV enthält keine fehlenden Clients
- [ ] Scan stoppt am Ende der Tabelle
- [ ] Stop-Button unterbricht Scan sofort

## Notes

- `vision.take_screenshot()` wird für Preprocessing NICHT mehr verwendet (nur noch für den Bot-Loop). Die Funktion bleibt unverändert.
- `vision.get_column_positions()` wird für Preprocessing NICHT mehr benötigt. Die Funktion bleibt unverändert (wird noch vom Bot-Loop genutzt).
- `row_height: 43.5` (float) — PIL's `crop()` truncated floats automatisch zu int, wie `debug_ocr.py` es tut.
- `overlap_rows: 9` basiert auf User-Beobachtung: 20 sichtbare Rows, nach Scroll sind 9 von vorheriger Seite noch sichtbar, 11 neue.
- Die `seen_keys` Dedup bleibt als Safety-Net erhalten, selbst wenn der Overlap-Skip korrekt funktioniert.

## Confidence Score: 9/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 10 | `debug_ocr.py` ist die exakte Referenzimplementierung |
| **External Knowledge** | 10 | Alles intern, keine neuen Libraries |
| **Risk** | 8 | Minimales Risiko — bewährter Ansatz wird übernommen |
| **Dependencies** | 8 | 3 Module betroffen, aber klar abgegrenzt und rückwärtskompatibel |
| **Clarity** | 9 | Anforderungen vom User klar beschrieben |
| **Testability** | 8 | Unit-Tests mit Mocks, E2E nur manuell gegen TaxAct |

**Overall: 9/10** — Der `debug_ocr.py`-Ansatz ist bewährt und wird 1:1 übernommen. Der Overlap-Skip ist eine einfache Range-Änderung. Sehr geringes Risiko.
