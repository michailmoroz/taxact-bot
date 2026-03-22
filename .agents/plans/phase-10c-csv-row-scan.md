# Plan: Phase 10c — CSV-basierte Row-by-Row Scan-Logik

## User Story

Als Steuerberater moechte ich, dass der Bot im CSV-Modus die Client-Tabelle zeilenweise scannt (Name, SSN/EIN, Return Type per OCR), den Status ausschliesslich aus der CSV bestimmt (nicht aus TaxAct's Fed EF Status), und bei keinem TODO-Client auf der Seite per Refocus-Click + Arrow-Down scrollt — analog zum Preprocessing.

## Acceptance Criteria

- [ ] Bot nimmt EINEN Screenshot pro Seite und croppt daraus zeilenweise (3 Spalten: client_name, ssn_ein, return_type)
- [ ] Fed EF Status wird NICHT aus TaxAct gelesen — CSV ist einzige Status-Quelle
- [ ] CSV-Lookup per Composite-Key `(name, ssn_ein, return_type)` bestimmt ob TODO
- [ ] Erster TODO-Client wird sofort bearbeitet (kein weiteres Scannen der Seite)
- [ ] Nicht-TODO Clients werden uebersprungen (naechste Zeile im selben Screenshot)
- [ ] Clients nicht in CSV werden uebersprungen (unbekannt)
- [ ] Falscher Return Type wird uebersprungen
- [ ] Nach 20 Zeilen ohne TODO: Refocus-Click `(refocus_click_x, refocus_click_y)` + `pydirectinput.press('down')` + neue Seite scannen
- [ ] End-of-Table Erkennung: letzter Client-Name unveraendert nach Scroll → fertig
- [ ] Spalten-Koordinaten direkt aus `settings["client_table"]["columns"]` (kein Template-Matching)
- [ ] `Ctrl+Home` Scroll-to-Top bleibt bei jeder Iteration (wie bisher)
- [ ] In-Memory Modus (ohne CSV) bleibt als Fallback funktionsfaehig
- [ ] Auto-Status-Update Feature entfernt (Fed EF Status wird nicht mehr gelesen)
- [ ] 1120S/1120/1040 Prozesse weiterhin funktionsfaehig

## Context

Die aktuelle `_scan_visible_clients` macht pro Zelle einen separaten Live-Screenshot + OCR via `_read_single_cell()`. Bei 20 Zeilen x 3-4 Spalten sind das 60-80 einzelne Screenshot+OCR Aufrufe pro Seite — extrem langsam. Der neue Ansatz: EIN Screenshot pro Seite, daraus zeilenweise croppen (3 Spalten pro Zeile), CSV-Lookup statt Fed-EF-Status lesen. Die Scroll-Logik liegt im `bot_controller._run()` (nicht in vision.py), da vision nur lesen soll. Die alte `_scan_visible_clients` + `find_next_client` bleiben fuer den in-memory Modus unberuehrt.

## Research Summary

### Relevant Files
| File | Purpose | Key Lines |
|------|---------|-----------|
| `clickbot/vision.py` | `read_all_rows_from_screenshot` — Screenshot-Crop-OCR Pattern | L833-907 |
| `clickbot/vision.py` | `_scan_visible_clients` — aktueller per-cell Scan (bleibt fuer in-memory) | L910-1041 |
| `clickbot/vision.py` | `find_next_client` — aktueller Scroll-Loop (bleibt fuer in-memory) | L1044-1141 |
| `clickbot/vision.py` | `normalize_return_type` — OCR Return-Type Normalisierung | L639-664 |
| `clickbot/vision.py` | `ClientRow` Dataclass | L618-626 |
| `clickbot/bot_controller.py` | `_run()` — Main Bot-Loop, CSV-Modus und in-memory | L194-351 |
| `clickbot/bot_controller.py` | `_scroll_table_to_top()` — Ctrl+Home | L162-172 |
| `clickbot/preprocessor.py` | Refocus-Click + Arrow-Down Scroll | L174-183 |
| `clickbot/preprocessor.py` | `ClientRecord` Dataclass | L29-35 |
| `config/settings.json` | `client_table.columns` (x, width pro Spalte) | L49-60 |
| `config/settings.json` | `preprocessing.refocus_click_x/y` | L78-79 |
| `tests/unit/test_csv_integration.py` | Bestehende CSV-Tests | L1-423 |

### Patterns to Follow

- **Screenshot-Crop-OCR** (vision.py:854-907): Ein PIL-Screenshot, `screenshot.crop((x, y, x+w, y+h))`, RGB→GRAY via cv2, `pytesseract.image_to_string()`. Gleiche OCR-Bereinigung: Unicode-Stripping, trailing chars, SSN Leading Zero.
- **Refocus + Scroll** (preprocessor.py:174-183): `pyautogui.click(refocus_x, refocus_y)` + `stop_event.wait(0.2)` + `pydirectinput.press('down')` + `stop_event.wait(post_scroll_delay)`.
- **End-of-Table Detection** (preprocessor.py:157-172): Vergleich `last_client_on_page == prev_last_client`. Bei 3 aufeinanderfolgenden Stale-Counts → break.
- **CSV-Lookup** (vision.py:949-959): `skip_keys` Set aus non-TODO Records, `csv_lookup` Dict.

## Dependencies

- **New Packages**: none (`pydirectinput` ist bereits installiert, wird in preprocessor.py verwendet)
- **Affected Modules**: `vision.py` (neue Funktion), `bot_controller.py` (geaenderter Loop)
- **Breaking Changes**: Nein — in-memory Modus bleibt unveraendert. Auto-Status-Update Feature wird entfernt (war experimentell, nie produktiv genutzt).

## Tasks

### Task 1: ADD `clickbot/vision.py` — Neue Funktion `scan_visible_clients_csv`

- **Action**: ADD
- **Implement**: Neue oeffentliche Funktion nach `read_all_rows_from_screenshot` (nach L907) einfuegen:

  ```python
  def scan_visible_clients_csv(
      screenshot: Image.Image,
      settings: dict,
      csv_records: list,
      selected_return_type: str,
      stop_event: Optional[threading.Event] = None,
  ) -> Tuple[Optional[ClientRow], Optional[Tuple[int, int]], str]:
      """Scan visible rows from screenshot for first TODO client (CSV mode).

      Takes a pre-captured screenshot and reads rows one by one by cropping
      cells for client_name, ssn_ein, and return_type. Looks up each row
      in csv_records by composite key. Returns the first TODO client found.

      Does NOT read fed_ef_status from TaxAct — CSV is the sole status source.

      Args:
          screenshot: Full-screen PIL screenshot (RGB)
          settings: Settings dict with client_table config
          csv_records: List of ClientRecord from CSV
          selected_return_type: Return type chosen by user in GUI
          stop_event: Optional stop signal

      Returns:
          (ClientRow, click_pos, last_client_name) if TODO found,
          (None, None, last_client_name) otherwise.
      """
  ```

  Logik (analog zu `read_all_rows_from_screenshot` L854-907):
  1. Lese `row_height`, `first_data_row_y`, `max_visible_rows` aus `settings["client_table"]`
  2. Lese Spalten-Koordinaten aus `settings["client_table"]["columns"]` (NUR `client_name`, `ssn_ein`, `return_type`)
  3. Build `skip_keys`: `{(r.client_name, r.client_id, r.return_type) for r in csv_records if r.status != "TODO"}`
  4. Build `csv_keys`: `{(r.client_name, r.client_id, r.return_type) for r in csv_records}` — fuer "Client in CSV?" Check
  5. `last_client_name = ""`
  6. Fuer jede Zeile `row_idx` in `range(max_visible_rows)`:
     a. Check `stop_event`
     b. `row_y = first_data_row_y + (row_idx * row_height)`
     c. Crop + OCR fuer `client_name` (gleiche Technik wie L876-886):
        - `region = screenshot.crop((x, row_y, x + w, row_y + row_height))`
        - `region_np = np.array(region)`
        - `region_gray = cv2.cvtColor(region_np, cv2.COLOR_RGB2GRAY)`
        - `region_pil = Image.fromarray(region_gray)`
        - `text = pytesseract.image_to_string(region_pil, lang="eng").strip()`
        - `lines = [l.strip() for l in text.split("\n") if l.strip()]`
        - `client_name = lines[0] if lines else ""`
     d. Wenn `client_name` leer → `continue` (kein break — Luecken moeglich)
     e. OCR-Bereinigung (wie L893-900): `client_name.lstrip("\u2018\u2019\u201c\u201d").rstrip(".,_")`
     f. `last_client_name = client_name`
     g. Crop + OCR fuer `ssn_ein` (gleiche Technik)
     h. SSN Leading-Zero Fix (wie L898-900): `re.match(r"^\d{2}-\d{2}-\d{4}$")` → `"0" + ssn_ein`
     i. Crop + OCR fuer `return_type` (gleiche Technik)
     j. `return_type = normalize_return_type(raw_return_type)`
     k. Wenn `return_type != selected_return_type` → `continue` (falscher Typ)
     l. `key = (client_name, ssn_ein, return_type)`
     m. Wenn `key not in csv_keys` → `continue` (unbekannter Client, log debug)
     n. Wenn `key in skip_keys` → `continue` (nicht TODO, log debug)
     o. **TODO gefunden!**
        - `click_x = columns["client_name"]["x"] + columns["client_name"]["width"] // 2`
        - `click_y = int(row_y + row_height // 2)`
        - `click_pos = (click_x, click_y)`
        - ClientRow bauen: `ClientRow(row_index=row_idx, y_position=int(row_y), client_name=client_name, return_type=return_type, fed_ef_status="", client_id=ssn_ein)`
        - `return (row_data, click_pos, last_client_name)`
  7. Kein TODO gefunden → `return (None, None, last_client_name)`

  Die OCR-Crop-Helferlogik (Schritte c-f) wiederholt sich fuer 3 Spalten. Extrahiere eine lokale Hilfsfunktion `_crop_and_ocr(col_name)` innerhalb der Funktion, um Duplikation zu vermeiden.

- **Pattern**: `read_all_rows_from_screenshot` (vision.py:854-907)
- **Depends on**: none
- **Validate**: `python -c "from clickbot.vision import scan_visible_clients_csv; print('OK')"`

### Task 2: UPDATE `clickbot/bot_controller.py` — CSV-Scan mit Scroll-Loop in `_run()`

- **Action**: UPDATE
- **Implement**:

  **Aenderung 1** — Import hinzufuegen (nach L15 `import pyautogui`):
  ```python
  import pydirectinput
  ```

  **Aenderung 2** — CSV-Modus Block (L245-258) ersetzen. Den gesamten Block:
  ```python
  if csv_records is not None:
      find_result = vision.find_next_client(
          self.settings,
          selected_return_type=self.selected_return_type,
          csv_records=csv_records
      )
      client_result, status_updates = find_result

      # Process auto-status-updates
      if status_updates:
          for name, cid, rtype, new_status in status_updates:
              update_client_status(self.csv_path, name, cid, rtype, new_status)
              self._send_log(f"Status updated: {name} -> {new_status}")
          csv_records = load_csv(self.csv_path)
  else:
      client_result = vision.find_next_client(
          self.settings,
          selected_return_type=self.selected_return_type,
          processed_clients=tracker.processed
      )
  ```

  Ersetzen durch:
  ```python
  if csv_records is not None:
      # CSV mode: scan page by page with screenshot-crop approach
      preprocessing_cfg = self.settings.get("preprocessing", {})
      refocus_x = preprocessing_cfg.get("refocus_click_x", 200)
      refocus_y = preprocessing_cfg.get("refocus_click_y", 1065)
      post_scroll_delay = preprocessing_cfg.get("post_scroll_delay_s", 0.5)
      max_scroll = self.settings.get("loop", {}).get(
          "scroll_in_table", {}
      ).get("max_attempts", 20)

      client_result = None
      last_seen_client = ""
      stale_count = 0

      for scroll_attempt in range(max_scroll + 1):
          if self.stop_event.is_set():
              break

          screenshot = pyautogui.screenshot()
          row_data, click_pos, last_client = vision.scan_visible_clients_csv(
              screenshot, self.settings, csv_records,
              self.selected_return_type, self.stop_event,
          )

          if row_data is not None:
              client_result = (row_data, click_pos)
              break

          # End-of-table detection (like preprocessor.py:157-172)
          if last_client == last_seen_client:
              stale_count += 1
              if stale_count >= 3:
                  logger.info(
                      f"End of table: last client '{last_client}' "
                      f"unchanged after {stale_count} attempts"
                  )
                  break
          else:
              stale_count = 0
          last_seen_client = last_client

          # Scroll: refocus click + arrow down (like preprocessor.py:174-183)
          if scroll_attempt < max_scroll:
              logger.debug(
                  f"No TODO on page, scrolling "
                  f"(attempt {scroll_attempt + 1}/{max_scroll})"
              )
              pyautogui.click(refocus_x, refocus_y)
              self.stop_event.wait(0.2)
              pydirectinput.press('down')
              self.stop_event.wait(post_scroll_delay)
  else:
      client_result = vision.find_next_client(
          self.settings,
          selected_return_type=self.selected_return_type,
          processed_clients=tracker.processed
      )
  ```

  **Keine weiteren Aenderungen noetig** — der Rest von `_run()` (L266-351) bleibt identisch:
  - `if client_result is None: break` (all done)
  - `client_row, click_pos = client_result`
  - Double-click, process, CSV update, etc.

  `_scroll_table_to_top()` (L239) bleibt bei jeder Iteration (wie bisher).

- **Pattern**: Preprocessing Scroll-Loop (preprocessor.py:99-183), bestehender `_run()` (bot_controller.py:232-349)
- **Depends on**: Task 1
- **Validate**: `python -c "from clickbot.bot_controller import BotController; print('OK')"`

### Task 3: UPDATE `tests/unit/test_csv_integration.py` — Tests fuer neue Scan-Logik

- **Action**: UPDATE
- **Implement**:

  **1. Neue Testklasse `TestScanVisibleClientsCsvNew`** (nach L275):

  Alle Tests mocken `pyautogui.screenshot()` mit einem PIL-Image und `pytesseract.image_to_string()` fuer die OCR-Ergebnisse.

  Hilfsfunktion in der Klasse:
  ```python
  def _make_screenshot(self):
      """Create a minimal PIL Image for mocking."""
      return Image.new("RGB", (1920, 1080), color=(255, 255, 255))
  ```

  Tests:
  - **`test_finds_todo_client`**: CSV hat `("JONES INC", "98-765", "1040", "TODO")`. OCR liefert gleiche Werte → ClientRow wird zurueckgegeben mit client_name, client_id, click_pos.
  - **`test_skips_non_todo_client`**: CSV hat Status "Submitted" → row wird uebersprungen, return None.
  - **`test_skips_client_not_in_csv`**: OCR-gelesener Client existiert nicht in CSV → skip.
  - **`test_skips_wrong_return_type`**: OCR liest return_type "1120S", selected ist "1040" → skip.
  - **`test_empty_client_name_continues`**: Leerer client_name → continue (kein break), naechste Zeile.
  - **`test_stop_event_interrupts_scan`**: `stop_event.is_set()` → sofortiger Abbruch.
  - **`test_ocr_cleanup_applied`**: Unicode-Prefix, trailing dots, SSN leading zero werden bereinigt.
  - **`test_returns_last_client_name`**: `last_client_name` korrekt gesetzt fuer End-of-Table Detection.

  **2. Neue Testklasse `TestBotControllerCsvScanLoop`** (nach den neuen Tests):

  Tests fuer den Scroll-Loop in `_run()`:
  - **`test_csv_mode_uses_scan_visible_clients_csv`**: Mock `vision.scan_visible_clients_csv` → wird aufgerufen.
  - **`test_csv_mode_scrolls_on_no_todo`**: Erster Aufruf liefert None → `pyautogui.click(refocus_x, refocus_y)` + `pydirectinput.press('down')` aufgerufen.
  - **`test_csv_mode_end_of_table_detection`**: 3x gleicher `last_client` → Loop bricht ab.
  - **`test_csv_mode_does_not_call_find_next_client`**: `vision.find_next_client` wird NICHT aufgerufen im CSV-Modus.

  **3. Bestehende Tests beibehalten**:
  - `TestScanVisibleClientsCsv` (L83-275) — testet alte `_scan_visible_clients` mit CSV → bleibt (in-memory Fallback)
  - `TestBackwardCompatibility` (L389-423) — testet `find_next_client` ohne CSV → bleibt
  - `TestBotControllerCsvPath` (L45-60) — bleibt
  - `TestCsvStatusWrites` (L280-358) — bleibt

- **Pattern**: Bestehende Tests in test_csv_integration.py (L83-275)
- **Depends on**: Tasks 1-2
- **Validate**: `pytest tests/unit/test_csv_integration.py -v`

## Testing Requirements

- [ ] `scan_visible_clients_csv`: TODO-Client korrekt erkannt (Screenshot-Crop)
- [ ] `scan_visible_clients_csv`: Nicht-TODO uebersprungen (Submitted, Accepted, etc.)
- [ ] `scan_visible_clients_csv`: Falscher Return Type uebersprungen
- [ ] `scan_visible_clients_csv`: Client nicht in CSV uebersprungen
- [ ] `scan_visible_clients_csv`: OCR-Bereinigung (Unicode, trailing dots, SSN leading zero)
- [ ] `scan_visible_clients_csv`: stop_event unterbricht sofort
- [ ] `scan_visible_clients_csv`: last_client_name korrekt fuer End-of-Table Detection
- [ ] `bot_controller._run()`: CSV-Modus nutzt neue Scan-Funktion
- [ ] `bot_controller._run()`: Scrollt bei keinem TODO auf Seite
- [ ] `bot_controller._run()`: End-of-Table nach 3 Stale-Counts
- [ ] Backward-Kompatibilitaet: In-Memory Modus unveraendert
- [ ] Edge case: Alle Clients non-TODO → "All done!"
- [ ] Edge case: stop_event waehrend Scan → sofortiger Abbruch

**Test Levels**: Unit (mocked pyautogui.screenshot + pytesseract)

## Bug Handling

- Bugs durch DIESE Aenderungen → sofort fixen
- Vorbestehende Bugs → in `.agents/bugs/` dokumentieren, NICHT fixen
- NIEMALS `1040.json`, `1120.json`, `1120S.json` aendern
- `_scan_visible_clients` und `find_next_client` (alt) NICHT aendern — bleiben fuer in-memory Modus

## Rollback Strategy

1. `git stash` oder `git checkout .` zum Revert
2. Alte Funktionen (`_scan_visible_clients`, `find_next_client`) bleiben bestehen
3. `csv_records=None` → altes Verhalten (in-memory Tracking via `find_next_client`)

## Manual Verification

- [ ] Bot mit CSV + 1040: Scannt zeilenweise, findet TODO-Client schnell (<5s pro Seite)
- [ ] Bot mit CSV + 1040: Nicht-TODO Clients im Log als "skipping" angezeigt
- [ ] Bot mit CSV + 1040: Scrollt nach unten wenn keine TODOs auf erster Seite
- [ ] Bot mit CSV + 1040: End-of-Table erkannt wenn keine TODOs mehr
- [ ] Bot mit CSV + 1040: Bearbeiteter Client → CSV Status = "Submitted"
- [ ] Bot mit CSV + 1040: 2-3 Clients im Loop → alle korrekt
- [ ] Bot mit CSV + 1120S: Funktioniert weiterhin (Regression)
- [ ] Bot ohne CSV (Fallback): Altes Verhalten wie bisher

## Notes

- **Architektur-Entscheidung**: Scroll-Logik liegt in `bot_controller._run()`, NICHT in vision.py. Vision bleibt rein lesend (keine Aktionen). `scan_visible_clients_csv` scannt nur eine Seite aus einem uebergebenen Screenshot.
- **Kein `find_next_client_csv`**: Der Scroll-Loop ist inline in `_run()`. Die Funktion `find_next_client` bleibt unveraendert fuer den in-memory Modus.
- **Auto-Status-Update entfernt**: Der Bot liest Fed EF Status nicht mehr aus TaxAct. Bei Bedarf kann ein neues Preprocessing gemacht werden, um TaxAct-Status zu aktualisieren.
- **`get_column_positions()` nicht aufgerufen im CSV-Modus**: Spalten-Koordinaten kommen direkt aus `settings["client_table"]["columns"]`. Das spart den Template-Matching Overhead (~1-2s).
- **Stale-Count = 3 fuer End-of-Table** (wie Preprocessing): Nicht 1, weil OCR gelegentlich den letzten Client-Namen leicht anders liest. 3 aufeinanderfolgende identische Ergebnisse sind ein zuverlaessigerer Indikator.
- **`pydirectinput` Import in bot_controller.py**: Noetig fuer `press('down')`. Ist bereits als Dependency installiert (verwendet in preprocessor.py).

## Confidence Score: 8/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 9/10 | Screenshot-Crop-OCR Pattern existiert in `read_all_rows_from_screenshot`, Scroll-Pattern in Preprocessing |
| **External Knowledge** | 10/10 | Pure Python, kein externes Wissen noetig |
| **Risk** | 7/10 | OCR-Konsistenz zwischen Preprocessing und Bot-Scan muss identisch sein; Scroll-Timing koennte Tuning brauchen |
| **Dependencies** | 9/10 | 2 Dateien + Tests, klare Abgrenzung zum in-memory Modus |
| **Clarity** | 8/10 | Logik klar, Architektur-Entscheidung (Scroll in bot_controller) eindeutig |
| **Testability** | 8/10 | Screenshot-Crop gut mockbar via PIL Image, E2E braucht TaxAct |

**Overall: 8/10** — Bewaehrte Patterns aus Preprocessing und read_all_rows_from_screenshot, saubere Trennung Vision/Controller. Groesste Unsicherheit: OCR-Konsistenz und Scroll-Timing bei vielen Seiten.
