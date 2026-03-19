# Plan: Phase 10a — Preprocessing & CSV Export

## User Story

Als Steuerberater möchte ich per GUI-Button die komplette TaxAct Client-Tabelle scannen und als CSV exportieren, damit ich eine deduplizierte Übersicht aller Clients mit Status habe.

## Acceptance Criteria

- [ ] GUI zeigt "Preprocessing"-Button oberhalb "Start Bot" (gleiche Größe, Farbe: blau/accent)
- [ ] GUI zeigt File-Picker (Label + Browse-Button) für CSV-Auswahl
- [ ] Beim App-Start wird automatisch die letzte generierte CSV geladen (wenn vorhanden)
- [ ] Preprocessing scannt komplette TaxAct-Tabelle via OCR (alle 4 Spalten)
- [ ] CSV-Datei wird unter `C:\TaxActBot\logs\clients_YYYY-MM-DD-HH-MM-SS.csv` gespeichert
- [ ] Duplikate (gleicher Name+ID+Return Type) werden dedupliziert (nur erster Eintrag)
- [ ] Status-Mapping: Fed EF Status leer → `TODO`, nicht leer → `DONE`
- [ ] Erneutes Preprocessing generiert neue Datei (Timestamp)
- [ ] Fortschritts-Updates im GUI-Log während Preprocessing
- [ ] Bestehende Bot-Funktionalität (Start Bot) bleibt unverändert

## Context

Phase 10a erstellt die Preprocessing-Infrastruktur: GUI-Button, Tabelle scannen, CSV erstellen, File-Picker. Der bestehende Bot-Loop wird NICHT verändert — das passiert in Phase 10b. So können wir das Preprocessing isoliert testen bevor wir den Bot-Loop umbauen.

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `clickbot/gui.py` | GUI-Layout, Buttons, State Machine | L129-178 (Control Card), L248-286 (Layout) |
| `clickbot/vision.py` | OCR, `_read_single_cell()`, `get_column_positions()` | L672-710 (headers), L772-803 (cell reading) |
| `clickbot/bot_controller.py` | Message Queue Pattern, Thread-Pattern | L166-184 (send helpers) |
| `config/settings.json` | client_table Spalten-Konfiguration | L49-59 |
| `debug_ocr.py` | Referenz für Table-Scanning | L73-108 (row scanning loop) |
| `clickbot/paths.py` | Pfadauflösung | L66-70 (`get_log_dir`) |

### Patterns to Follow
- **Table Scanning**: `debug_ocr.py:73-108` — iteriert Zeilen via `first_data_row_y + row_idx * row_height`, liest Zellen via `settings.json:client_table.columns`
- **OCR Cell Reading**: `vision.py:772-803` (`_read_single_cell`) — Grayscale-Konvertierung für farbigen Text
- **GUI Button Pattern**: `gui.py:166-178` — CTkButton mit Farbe, Font, Command, Height=48
- **GUI Layout Grid**: `gui.py:248-286` — Row-basiertes Grid-Layout
- **Message Queue**: `bot_controller.py:166-184` — `_send_log/status/progress/error/complete`
- **Thread Pattern**: `bot_controller.py:72-89` — Thread mit stop_event + message_queue

## Dependencies

- **New Packages**: none
- **Affected Modules**: `gui.py`, `vision.py`, `paths.py`, `settings.json`
- **New Modules**: `clickbot/preprocessor.py`
- **Breaking Changes**: Nein — bestehender Bot-Loop bleibt unverändert

## Tasks

### Task 1: UPDATE `config/settings.json` — Preprocessing Config

- **Action**: UPDATE
- **Implement**: `preprocessing` Abschnitt hinzufügen:
  ```json
  "preprocessing": {
    "csv_output_dir": "C:/TaxActBot/logs",
    "scroll_delay_s": 0.5
  }
  ```
  SSN/EIN-Spalte ist bereits in settings.json vorhanden (x=400, width=120).
- **Pattern**: `settings.json:49-59`
- **Depends on**: none
- **Validate**: `python -c "import json; d=json.load(open('config/settings.json')); assert 'preprocessing' in d; print('OK')"`

### Task 2: UPDATE `clickbot/paths.py` — CSV-Verzeichnis

- **Action**: ADD
- **Implement**: Neue Convenience-Funktion:
  ```python
  def get_csv_dir() -> Path:
      """Path to preprocessing CSV output directory."""
      csv_dir = Path("C:/TaxActBot/logs")
      csv_dir.mkdir(parents=True, exist_ok=True)
      return csv_dir
  ```
- **Pattern**: `paths.py:66-70` (`get_log_dir`)
- **Depends on**: none
- **Validate**: `python -c "from clickbot.paths import get_csv_dir; print(get_csv_dir())"`

### Task 3: UPDATE `clickbot/vision.py` — `get_column_positions()` erweitern

- **Action**: UPDATE
- **Implement**:
  1. Optionaler Parameter `extra_columns: Optional[List[str]] = None` an `get_column_positions()` hinzufügen
  2. Wenn `extra_columns` angegeben, werden diese zusätzlich zu den Standard-3 Spalten gesucht
  3. Template für SSN/EIN: `"ssn_ein": "common/column_header_ssn_ein.png"`
  4. Bestehender Aufruf ohne Parameter verhält sich identisch (keine Breaking Change)

  ```python
  def get_column_positions(
      extra_columns: Optional[List[str]] = None
  ) -> Optional[Dict[str, Tuple[int, int]]]:
      header_templates = {
          "client_name": "common/column_header_client_name.png",
          "return_type": "common/column_header_return_type.png",
          "fed_ef_status": "common/column_header_fed_ef_status.png",
      }
      if extra_columns:
          extra_map = {
              "ssn_ein": "common/column_header_ssn_ein.png",
          }
          for col in extra_columns:
              if col in extra_map:
                  header_templates[col] = extra_map[col]
      # ... rest unchanged
  ```

- **Pattern**: `vision.py:672-710`
- **Depends on**: none (Screenshot `column_header_ssn_ein.png` bereits vorhanden)
- **Validate**: `python -c "from clickbot.vision import get_column_positions; print('OK')"`

### Task 4: CREATE `clickbot/preprocessor.py`

- **Action**: CREATE
- **Implement**: Neues Modul für Preprocessing. Nutzt `vision._read_single_cell()` und `vision.get_column_positions()`.

  **Dataclass:**
  ```python
  @dataclass
  class ClientRecord:
      client_name: str
      client_id: str      # SSN/EIN
      return_type: str
      status: str          # TODO, DONE, FAIL
  ```

  **Funktionen:**

  1. `preprocess_table(settings, message_queue, stop_event) -> Optional[Path]`
     - Wird im Thread ausgeführt (analog BotController._run)
     - Konfiguriert vision module (`vision.configure()`, `vision.configure_tesseract()`)
     - Scrollt Tabelle nach oben (Ctrl+Home, analog `bot_controller._scroll_table_to_top()`)
     - Findet Column-Headers via `get_column_positions(extra_columns=["ssn_ein"])`
     - Iteriert zeilenweise (analog `debug_ocr.py:73-108`):
       - Für jede Zeile: `_read_single_cell()` für alle 4 Spalten
       - Leere `client_name` → Ende der sichtbaren Daten, stoppe Zeilen-Scan
       - `return_type` normalisieren via `normalize_return_type()`
       - Speichert als `ClientRecord`
     - Scrollt runter, wiederholt bis Ende (last_client_name unchanged detection, analog `find_next_client`)
     - Fortschritts-Updates via `message_queue.put(StatusMessage("log", f"Scanned {count} clients..."))`
     - Dedupliziert via `(client_name, client_id, return_type)` als Set-Key
     - Status-Mapping: `fed_ef_status` leer → `TODO`, nicht leer → `DONE`
     - Erstellt `C:\TaxActBot\logs\` Verzeichnis falls nötig
     - Schreibt CSV mit Timestamp: `clients_YYYY-MM-DD-HH-MM-SS.csv`
     - Gibt Pfad zur erstellten CSV zurück (oder None bei Fehler/Stop)

  2. `load_csv(csv_path: Path) -> List[ClientRecord]`
     - Liest CSV via `csv.DictReader`
     - Gibt Liste von `ClientRecord` zurück

  3. `update_client_status(csv_path: Path, client_name: str, client_id: str, return_type: str, new_status: str) -> None`
     - Liest CSV, findet Zeile via `(name, id, return_type)`, setzt Status, schreibt CSV zurück

  4. `get_todo_clients(csv_path: Path, return_type: str) -> List[ClientRecord]`
     - Filtert: `record.return_type == return_type and record.status == "TODO"`

  5. `get_latest_csv(csv_dir: Path) -> Optional[Path]`
     - Glob für `clients_*.csv`, sortiert nach Name (= Timestamp), gibt neueste zurück

- **Pattern**: `debug_ocr.py:73-108` (Scanning), `vision.py:772-803` (Cell-Reading), `bot_controller.py:186-210` (Thread + Message Queue)
- **Depends on**: Task 2, Task 3
- **Validate**: `python -c "from clickbot.preprocessor import preprocess_table, load_csv, update_client_status, get_todo_clients, get_latest_csv, ClientRecord; print('OK')"`

### Task 5: UPDATE `clickbot/gui.py` — Preprocessing-Button + File-Picker

- **Action**: UPDATE
- **Implement**:
  1. **GUIState**: Neuer State `PREPROCESSING = "preprocessing"`

  2. **_create_widgets()**: Neue Widgets:
     - `preprocessing_frame` (Card, gleicher Stil wie `control_frame`)
     - `preprocessing_button`: CTkButton, height=48, Farbe `COLORS["accent"]` (#2563eb), Text "Scan Client Table"
     - `csv_file_frame`: Innerer Frame mit horizontalem Layout
     - `csv_path_label`: CTkLabel, zeigt aktuellen CSV-Pfad (truncated, `.../{filename}`), initial "No CSV loaded"
     - `csv_browse_button`: CTkButton, klein, Text "Browse", öffnet File-Dialog
     - `csv_status_label`: CTkLabel, zeigt z.B. "47 TODO, 3 DONE, 0 FAIL"

  3. **_setup_layout()**: Row-Nummern anpassen:
     - Row 0: Header (unverändert)
     - Row 1: Return Type Card (unverändert)
     - Row 2: **Preprocessing Card** (NEU)
     - Row 3: Control Card (war Row 2)
     - Row 4: Status Card (war Row 3)
     - Row 5: Log Card (war Row 4, `grid_rowconfigure(5, weight=1)`)

  4. **Neue Methoden**:
     - `_on_preprocessing_click()`:
       - Setzt State auf PREPROCESSING
       - Deaktiviert Buttons (Preprocessing + Start)
       - Startet Thread mit `preprocessor.preprocess_table()`
       - Startet Polling (wie `_start_polling`)
       - Bei Completion: Lädt erstellte CSV, aktualisiert Labels
     - `_on_browse_csv()`:
       - `tkinter.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")], initialdir="C:/TaxActBot/logs")`
       - Bei Auswahl: `_load_csv_file(path)`
     - `_load_csv_file(path: Path)`:
       - `preprocessor.load_csv(path)` aufrufen
       - `csv_path_label` aktualisieren (zeigt `.../{filename}`)
       - `csv_status_label` aktualisieren (counts: TODO/DONE/FAIL)
       - Speichert `self._csv_path = path`
     - `_load_latest_csv()`:
       - `preprocessor.get_latest_csv()` aufrufen
       - Falls vorhanden: `_load_csv_file()` aufrufen
       - Aufgerufen in `__init__` nach Widget-Erstellung

  5. **_on_start_click()** erweitern: Prüft `self._csv_path` → wenn None: `_log("ERROR: No CSV loaded")` + return

  6. **Preprocessing/Start Button State Management**:
     - Während PREPROCESSING: beide Buttons disabled, Preprocessing-Button zeigt "Scanning..."
     - Während RUNNING: beide Buttons disabled (außer Stop)
     - READY: beide Buttons enabled

- **Pattern**: `gui.py:129-178` (Card/Button), `gui.py:248-286` (Layout), `gui.py:394-414` (`_start_bot`)
- **Depends on**: Task 4
- **Validate**: Manuell — GUI starten, Preprocessing-Button und File-Picker sichtbar

### Task 6: UPDATE `config/settings.json` — GUI-Höhe

- **Action**: UPDATE
- **Implement**: `gui.window_height` von 680 auf 820 erhöhen (Platz für Preprocessing Card)
- **Pattern**: `settings.json:42-48`
- **Depends on**: Task 5
- **Validate**: `python -c "import json; d=json.load(open('config/settings.json')); assert d['gui']['window_height'] >= 800; print('OK')"`

## Testing Requirements

- [ ] Unit: `preprocessor.py` — `load_csv` / `update_client_status` / `get_todo_clients` / `get_latest_csv`
- [ ] Unit: `preprocessor.py` — Deduplizierung bei gleichem (Name, ID, Return Type)
- [ ] Unit: `preprocessor.py` — Status-Mapping (leer → TODO, nicht-leer → DONE)
- [ ] Unit: `vision.py` — `get_column_positions(extra_columns=["ssn_ein"])` findet 4 Spalten
- [ ] Unit: `vision.py` — `normalize_return_type("1040")` → "1040" (bereits gefixt)
- [ ] Edge case: Leere Tabelle (0 Clients) → leere CSV
- [ ] Edge case: `get_latest_csv` mit leerem Verzeichnis → None

**Test Levels**: Unit

## Bug Handling

- Bugs caused by THESE changes → Fix immediately
- Pre-existing bugs → Document in `.agents/bugs/`, do NOT fix
- NEVER modify working code outside the scope of this plan

## Rollback Strategy

1. `git stash` or `git checkout .` to revert changes
2. Bestehender Bot-Loop ist nicht betroffen (keine Breaking Changes in 10a)

## Manual Verification

- [ ] GUI: Preprocessing-Button sichtbar oberhalb Start-Bot, blaue Farbe
- [ ] GUI: File-Picker mit Label und Browse-Button sichtbar
- [ ] GUI: Beim Start wird letzte CSV automatisch geladen (wenn vorhanden)
- [ ] Preprocessing: Klick auf Button → Tabelle wird gescannt → CSV erstellt
- [ ] CSV: Korrekte Spalten (Client, ID, Return Type, Status)
- [ ] CSV: Duplikate dedupliziert
- [ ] CSV: Status korrekt (TODO/DONE)
- [ ] File-Picker: Browse öffnet Windows Explorer, Datei laden funktioniert
- [ ] Bot-Start ohne CSV: Fehlermeldung im Log

## Notes

- **normalize_return_type()** ✅ bereits für 1040 gefixt (separates Pattern `[14]\d?40`)
- **SSN/EIN Koordinaten** ✅ kalibriert (x=400, width=120) und auf Remote-PC verifiziert
- **Grayscale OCR** ✅ in debug_ocr.py gefixt, muss auch in preprocessor.py verwendet werden (nutzt `vision._read_single_cell()` das bereits Grayscale macht)
- **Bestehender Bot-Loop bleibt unverändert** — CSV-Integration kommt erst in Phase 10b
- Phase 10a kann isoliert getestet werden ohne den Bot-Loop zu riskieren

## Confidence Score: 9/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 9 | debug_ocr.py als exakte Referenz, GUI-Patterns klar |
| **External Knowledge** | 9 | csv stdlib + tkinter.filedialog — trivial |
| **Risk** | 9 | Kein bestehender Code wird gebrochen, alles additiv |
| **Dependencies** | 8 | 4 Module betroffen (gui, vision, paths, settings) + 1 neues — kein Cascade-Risiko |
| **Clarity** | 9 | Alle Anforderungen geklärt, Koordinaten kalibriert |
| **Testability** | 8 | CSV-Logik voll testbar, GUI manuell verifizierbar |

**Overall: 9/10** — Kein bestehender Code wird gebrochen, alle Voraussetzungen erfüllt, klare Patterns. Nur GUI-Layout braucht manuelle Feinabstimmung.
