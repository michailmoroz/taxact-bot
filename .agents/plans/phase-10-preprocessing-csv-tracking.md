# Plan: Preprocessing & CSV Client Tracking

## User Story

Als Steuerberater möchte ich vor dem Bot-Start die komplette TaxAct Client-Tabelle als CSV exportieren und danach den Bot-Fortschritt persistent in dieser CSV nachverfolgen, damit Duplikate erkannt werden, kein Client doppelt bearbeitet wird und der Fortschritt über Neustarts hinweg erhalten bleibt.

## Acceptance Criteria

- [ ] GUI zeigt "Preprocessing"-Button oberhalb "Start Bot" (gleiche Größe, andere Farbe)
- [ ] Preprocessing scannt komplette TaxAct-Tabelle und erstellt CSV mit Client/ID/Return Type/Status
- [ ] CSV-Datei wird unter `C:\TaxActBot\logs\clients_YYYY-MM-DD-HH-MM-SS.csv` gespeichert
- [ ] Duplikate (gleicher Name+ID+Return Type) in TaxAct werden in CSV dedupliziert (nur erster Eintrag)
- [ ] GUI zeigt File-Picker (Label + Browse-Button) für CSV-Auswahl
- [ ] Beim Start wird automatisch die letzte generierte CSV geladen
- [ ] Bot-Start nur möglich wenn CSV geladen — sonst Fehlermeldung
- [ ] Nach jeder Iteration: Client in CSV als DONE (Erfolg) oder FAIL (Fehler) markiert
- [ ] Wenn Client+ID+Return Type als DONE → auch TaxAct-Duplikate werden übersprungen
- [ ] Erneutes Preprocessing überschreibt (generiert neue Datei mit Timestamp)
- [ ] Bestehende 1120S/1120/1040-Prozesse weiterhin funktionsfähig

## Context

Aktuell trackt der Bot Clients nur per Name in einem in-memory Set — keine Persistenz, keine Duplikat-Erkennung bei gleichen Namen mit verschiedenen IDs, kein Status-Tracking (DONE/FAIL). Das Preprocessing erstellt eine vollständige Client-Liste via OCR und bildet die Basis für persistentes, CSV-basiertes Tracking mit Composite Key (Name+SSN/EIN+Return Type).

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `clickbot/gui.py` | GUI-Layout, Buttons, State Machine | L129-178 (Return Type + Control Card), L248-286 (Layout) |
| `clickbot/vision.py` | OCR, Table Scanning, `_read_single_cell()` | L772-803 (cell reading), L806-895 (scan visible clients) |
| `clickbot/state.py` | In-memory ClientTracker (`Set[str]`) | L1-57 (gesamte Datei) |
| `clickbot/bot_controller.py` | Main Loop, `_run()`, mark_processed | L186-287 (`_run` method) |
| `config/settings.json` | client_table Spalten-Konfiguration | L49-59 |
| `debug_ocr.py` | Referenz-Script für Table-Scanning via settings.json | L73-108 (row scanning loop) |
| `clickbot/paths.py` | Pfadauflösung Dev/Exe | L66-70 (`get_log_dir`) |

### Patterns to Follow
- **Table Scanning**: `debug_ocr.py:73-108` — iteriert Zeilen via `first_data_row_y + row_idx * row_height`, liest Zellen via `settings.json:client_table.columns` (x, width)
- **OCR Cell Reading**: `vision.py:772-803` (`_read_single_cell`) — nutzt dynamische Column-Positions von Header-Templates + settings width
- **GUI Button Pattern**: `gui.py:166-178` (Start-Button) — CTkButton mit Farbe, Font, Command, Height
- **GUI Layout Grid**: `gui.py:248-286` — Row-basiertes Grid-Layout mit `pad_x`, `sticky="ew"`
- **Message Queue**: `bot_controller.py:166-184` — `_send_log/status/progress/error/complete` Muster

## Dependencies

- **New Packages**: none
- **Affected Modules**: `gui.py`, `vision.py`, `state.py`, `bot_controller.py`, `settings.json`, `paths.py`
- **New Modules**: `clickbot/preprocessor.py`
- **Breaking Changes**: Ja — `state.py` wird von `Set[str]` auf CSV-basiertes Tracking umgestellt. `bot_controller.py:_run()` muss CSV lesen/schreiben statt in-memory Set nutzen. `find_next_client()` Signatur ändert sich (bekommt CSV-Daten statt Set).

## Tasks

### Task 1: UPDATE `config/settings.json`

- **Action**: UPDATE
- **Implement**: Neue Spalte `ssn_ein` in `client_table.columns` hinzufügen. Position/Breite muss vom User kalibriert werden (vorläufig Platzhalter basierend auf Tabellenlayout — SSN/EIN-Spalte liegt typischerweise zwischen client_name und return_type).
  ```json
  "ssn_ein": { "x": 350, "width": 110 }
  ```
  Außerdem `preprocessing` Abschnitt zu settings.json hinzufügen:
  ```json
  "preprocessing": {
    "csv_output_dir": "C:/TaxActBot/logs",
    "arrow_key_delay_s": 0.3
  }
  ```
- **Pattern**: `settings.json:49-59` für bestehende Spalten-Konfiguration
- **Depends on**: none
- **Validate**: `python -c "import json; d=json.load(open('config/settings.json')); assert 'ssn_ein' in d['client_table']['columns']; assert 'preprocessing' in d; print('OK')"`

### Task 2: CREATE `clickbot/preprocessor.py`

- **Action**: CREATE
- **Implement**: Neues Modul für das Preprocessing. Kernfunktionalität:

  1. `preprocess_table(settings, message_queue, stop_event) -> Optional[Path]`
     - Hauptfunktion, wird im Thread ausgeführt
     - Scrollt Tabelle nach oben (Ctrl+Home)
     - Findet Column-Headers via Template Matching (`get_column_positions()` erweitert um `ssn_ein`)
       - **Harter Fehler**: Wenn Column-Headers (inkl. SSN/EIN) nicht gefunden → Fehlermeldung, return None
     - **Navigation via Pfeiltaste-Unten (row-by-row)**:
       - Klickt auf ersten Client in Tabelle (`first_data_row_y + row_height // 2`)
       - Trackt `current_visual_row` (startet bei 0)
       - Berechnet Lese-Position: `row_y = first_data_row_y + (current_visual_row * row_height)`
       - Liest alle 4 Spalten via `_read_single_cell()`: `client_name`, `ssn_ein`, `return_type`, `fed_ef_status`
       - Leere `client_name` → Ende der Tabelle
       - End-Detection: Wenn `(client_name, client_id, return_type)` identisch zum vorherigen → Ende
       - Speichert Row-Daten in Liste
       - Drückt Pfeiltaste-Unten, wartet kurz (`preprocessing.arrow_key_delay_s`, Default 0.3s)
       - `current_visual_row` inkrementiert bis `max_visible_rows - 1`, danach fix (Tabelle scrollt automatisch)
     - Dedupliziert via `(client_name, ssn_ein, return_type)` Composite Key
     - Status-Mapping: fed_ef_status leer → `TODO`, nicht leer → `DONE`
     - Schreibt CSV nach `C:\TaxActBot\logs\clients_YYYY-MM-DD-HH-MM-SS.csv`
     - Sendet Fortschritts-Updates via message_queue
     - Gibt Pfad zur erstellten CSV zurück

  2. `load_csv(csv_path: Path) -> List[ClientRecord]`
     - Liest CSV und gibt Liste von ClientRecord zurück

  3. `update_client_status(csv_path: Path, client_name: str, client_id: str, return_type: str, new_status: str) -> None`
     - Findet Client via Name+ID+Return Type, setzt Status, schreibt CSV zurück

  4. `get_todo_clients(csv_path: Path, return_type: str) -> List[ClientRecord]`
     - Filtert CSV nach Return Type + Status == TODO

  5. `@dataclass ClientRecord`:
     - `client_name: str`
     - `client_id: str` (SSN/EIN)
     - `return_type: str`
     - `status: str` (TODO/DONE/FAIL)

  Pattern: Scanning-Loop analog `debug_ocr.py:73-108`, OCR via `vision._read_single_cell()` (vision.py:772-803), CSV via stdlib `csv` Modul.

- **Pattern**: `debug_ocr.py:73-108` für Row-Scanning, `vision.py:772-803` für Cell-Reading
- **Depends on**: Task 1
- **Validate**: `python -c "from clickbot.preprocessor import preprocess_table, load_csv, update_client_status, get_todo_clients, ClientRecord; print('OK')"`

### Task 3: UPDATE `clickbot/vision.py` — Column-Header für SSN/EIN

- **Action**: UPDATE
- **Implement**:
  1. `get_column_positions()` (L672-710): `header_templates` Dict erweitern um `"ssn_ein": "common/column_header_ssn_ein.png"`
  2. Optionaler Parameter `extra_columns: List[str] = None` an bestehende Funktion, damit der normale Bot-Flow (find_next_client) nicht bricht wenn das SSN/EIN-Template nicht benötigt wird.
  3. **Harter Fehler bei extra_columns**: Wenn `extra_columns=["ssn_ein"]` angegeben und Template nicht gefunden → `get_column_positions()` gibt `None` zurück. Der Preprocessor bricht ab. Es wird NICHT ohne SSN/EIN weitergemacht.
  4. `normalize_return_type()` muss auch `1040` korrekt erkennen — ✅ bereits gefixt (Pattern `[14]\d?40`).

- **Pattern**: `vision.py:672-710` für bestehende Column-Header-Detection
- **Depends on**: Task 1 (settings.json Spalte), User muss Screenshot `common/column_header_ssn_ein.png` bereitstellen
- **Validate**: `python -c "from clickbot.vision import get_column_positions; print('OK')"`

### Task 4: REFACTOR `clickbot/state.py` — CSV-basiertes Tracking

- **Action**: REFACTOR
- **Implement**: `ClientTracker` erweitern um CSV-basiertes Tracking:
  1. Neuer Constructor-Parameter: `csv_path: Optional[Path] = None`
  2. `load_from_csv(csv_path)` — lädt CSV und baut internes Lookup-Dict `{(name, id, return_type): status}`
  3. `is_processed(client_name, client_id, return_type)` — prüft ob `(name, id, return_type)` Status != `TODO`
  4. `mark_done(client_name, client_id, return_type)` — setzt Status auf `DONE` in-memory + schreibt CSV
  5. `mark_failed(client_name, client_id, return_type)` — setzt Status auf `FAIL` in-memory + schreibt CSV
  6. `get_todo_clients(return_type)` — gibt Liste der TODO-Clients für gegebenen Return-Type
  7. Backward-Kompatibilität: Wenn `csv_path=None`, verhält sich wie bisher (in-memory Set) — für Tests und Fallback

- **Pattern**: `state.py:1-57` für bestehende Struktur
- **Depends on**: Task 2 (ClientRecord Dataclass, CSV-Format)
- **Validate**: `python -c "from clickbot.state import ClientTracker; t = ClientTracker(); print('OK')"`

### Task 5: UPDATE `clickbot/bot_controller.py` — CSV-Integration

- **Action**: UPDATE
- **Implement**:
  1. Constructor: Neuer Parameter `csv_path: Optional[Path] = None`
  2. `_run()` (L186-287):
     - `ClientTracker(csv_path=self.csv_path)` statt `ClientTracker()`
     - `tracker.load_from_csv()` vor Loop-Start
     - Nach `find_next_client`: Client via Name+ID+Return Type matchen statt nur Name
     - Nach erfolgreicher Iteration: `tracker.mark_done(name, id, return_type)` statt `tracker.mark_processed(name)`
     - Nach Fehler/Recovery: `tracker.mark_failed(name, id, return_type)`
  3. `find_next_client()` Aufruf anpassen: statt `processed_clients=tracker.processed` (Set) → neues Interface mit CSV-Daten
  4. Neuer Preprocessing-Modus: `run_preprocessing()` Methode die `preprocessor.preprocess_table()` aufruft

- **Pattern**: `bot_controller.py:186-287` für bestehenden Loop
- **Depends on**: Task 2, Task 4
- **Validate**: `python -c "from clickbot.bot_controller import BotController; print('OK')"`

### Task 6: UPDATE `clickbot/vision.py` — `find_next_client()` CSV-Integration

- **Action**: UPDATE
- **Implement**: `find_next_client()` und `_scan_visible_clients()` anpassen:
  1. Neuer Parameter: `todo_clients: Optional[List[ClientRecord]] = None`
  2. Wenn `todo_clients` gegeben: Client wird per Name+ID+Return Type geprüft
  3. OCR liest jetzt auch `ssn_ein` Spalte um Client zu identifizieren
  4. `_scan_visible_clients()` gibt `ClientRow` mit neuem Feld `client_id` (SSN/EIN) zurück
  5. `ClientRow` Dataclass erweitern: `client_id: str = ""` (backward-kompatibel)
  6. Matching-Logik: Row gilt als Match wenn `(client_name, client_id, return_type)` in todo_clients UND `fed_ef_status` leer

- **Pattern**: `vision.py:806-895` für bestehende Scan-Logik
- **WICHTIG — Return-Signatur beachten**: `_scan_visible_clients()` gibt ein **3-Tuple** zurück: `(ClientRow|None, click_pos|None, last_client_name: str)`. `find_next_client()` entpackt dieses 3-Tuple. Die Erweiterung muss dieses Format exakt beibehalten.
- **Depends on**: Task 3, Task 4
- **Validate**: `python -c "from clickbot.vision import ClientRow; r = ClientRow(0, 0, 'test', '1120S', '', client_id='12-345'); print('OK')"`

### Task 7: UPDATE `clickbot/gui.py` — Preprocessing-Button + File-Picker

- **Action**: UPDATE
- **Implement**:
  1. **GUIState**: Neuer State `PREPROCESSING = "preprocessing"` (L58-61)
  2. **_create_widgets()** (L117-246):
     - Neuer `preprocessing_frame` (Card) zwischen Return-Type-Card (Row 1) und Control-Card (Row 2)
     - `preprocessing_button`: CTkButton, gleiche Größe wie Start (height=48), Farbe `COLORS["accent"]` (blau)
     - `csv_file_frame`: Frame mit Label (zeigt CSV-Pfad, truncated) + Browse-Button
     - `csv_status_label`: Zeigt "No CSV loaded" / "Loaded: 47 TODO, 3 DONE"
  3. **_setup_layout()** (L248-286):
     - Row-Nummern anpassen: Preprocessing-Card auf Row 2, Control-Card auf Row 3, Status Row 4, Log Row 5
     - `self.grid_rowconfigure(5, weight=1)` statt Row 4
  4. **Neue Methoden**:
     - `_on_preprocessing_click()`: Startet Preprocessing im Thread. **Während Preprocessing**: Button zeigt "Scanning...", Log zeigt Fortschritt. **Bei Completion**: Lädt CSV, aktualisiert Labels mit Counts (X TODO, Y DONE), Log: "Preprocessing complete! Found X clients (Y TODO, Z DONE)", Sound: `play_complete()`. **Bei Fehler**: Log mit Fehlermeldung, Sound: `play_error()`, zurück auf READY.
     - `_on_browse_csv()`: Öffnet `tkinter.filedialog.askopenfilename(filetypes=[("CSV", "*.csv")], initialdir="C:/TaxActBot/logs")`
     - `_load_csv_file(path)`: Lädt CSV, aktualisiert Label + Status
     - `_load_latest_csv()`: Sucht neueste `clients_*.csv` in `C:\TaxActBot\logs\`, lädt sie
  5. **_on_start_click()**: Prüft ob CSV geladen → sonst Fehlermeldung + return
  6. **_start_bot()**: Übergibt `csv_path` an `BotController`
  7. **GUI-Höhe**: `window_height` in settings.json erhöhen (680 → 800) wegen neuem Card

- **Pattern**: `gui.py:129-178` für Card/Button-Erstellung, `gui.py:248-286` für Layout
- **Depends on**: Task 5 (BotController csv_path Parameter)
- **Validate**: Manuell — GUI starten, Preprocessing-Button und File-Picker sichtbar

### Task 8: UPDATE `config/settings.json` — GUI-Höhe anpassen

- **Action**: UPDATE
- **Implement**: `gui.window_height` von 680 auf 800 erhöhen
- **Pattern**: `settings.json:43-48`
- **Depends on**: Task 7
- **Validate**: `python -c "import json; d=json.load(open('config/settings.json')); assert d['gui']['window_height'] == 800; print('OK')"`

### Task 9: UPDATE `clickbot/paths.py` — CSV-Verzeichnis

- **Action**: UPDATE
- **Implement**: Neue Convenience-Funktion:
  ```python
  def get_csv_dir() -> Path:
      """Path to preprocessing CSV output directory."""
      csv_dir = Path("C:/TaxActBot/logs")
      csv_dir.mkdir(parents=True, exist_ok=True)
      return csv_dir
  ```
- **Pattern**: `paths.py:66-70` (get_log_dir)
- **Depends on**: none
- **Validate**: `python -c "from clickbot.paths import get_csv_dir; print(get_csv_dir())"`

## Testing Requirements

- [ ] Unit: `preprocessor.py` — CSV schreiben/lesen/updaten, Deduplizierung, Status-Mapping
- [ ] Unit: `state.py` — CSV-basiertes Tracking, `is_processed()` mit Name+ID+Return Type, `mark_done/mark_failed`
- [ ] Unit: `vision.py` — `ClientRow` mit `client_id` Feld, `normalize_return_type` für 1040
- [ ] Integration: Preprocessing → CSV → Bot-Start → Status-Update Roundtrip
- [ ] Edge case: Leere Tabelle (0 Clients)
- [ ] Edge case: Tabelle mit nur DONE-Clients (kein TODO übrig)
- [ ] Edge case: Duplikate mit gleichem Name+ID+Return Type in TaxAct → nur 1 CSV-Eintrag
- [ ] Edge case: CSV-Datei existiert nicht / ist korrupt beim Laden

**Test Levels**: Unit + Integration

## Bug Handling

During implementation:
- Bugs caused by THESE changes → Fix immediately
- Pre-existing bugs discovered → Document in `.agents/bugs/`, do NOT fix
- NEVER modify working code outside the scope of this plan

## Rollback Strategy

If implementation fails:
1. `git stash` or `git checkout .` to revert changes
2. `state.py` hat backward-kompatiblen Fallback (csv_path=None → in-memory Set)
3. `vision.py` ClientRow hat default `client_id=""` → bestehende Aufrufe brechen nicht

## Manual Verification

After implementation, manually verify:
- [ ] GUI: Preprocessing-Button sichtbar oberhalb Start-Bot, blaue Farbe
- [ ] GUI: File-Picker mit Label und Browse-Button sichtbar
- [ ] GUI: "Start Bot" zeigt Fehler wenn keine CSV geladen
- [ ] Preprocessing: Scannt TaxAct-Tabelle, erstellt CSV in `C:\TaxActBot\logs\`
- [ ] CSV: Korrekte Spalten (Client, ID, Return Type, Status), Duplikate dedupliziert
- [ ] Bot-Run: Nutzt CSV, markiert Clients als DONE/FAIL nach Iteration
- [ ] Bot-Run: Überspringt DONE-Clients (auch Duplikate)
- [ ] Neustart: Letzte CSV wird automatisch geladen

## Notes

- **Screenshot `common/column_header_ssn_ein.png`** ✅ vom User bereitgestellt
- **SSN/EIN Spalten-Koordinaten** vorläufig auf x=400, width=120 gesetzt — User kalibriert via `debug_ocr.py` auf Remote-PC
- **normalize_return_type()** muss für 1040 erweitert werden — "1040" wird aktuell nicht vom Regex `\d120(.)?` erkannt. Einfacher Fix: separate Prüfung auf `1040` Pattern
- **CSV-Pfad `C:\TaxActBot\logs\`** ist hardcoded pro Anforderung, aber auch in settings.json konfigurierbar (`preprocessing.csv_output_dir`)
- **Backward-Kompatibilität**: state.py und vision.py bleiben mit altem Interface nutzbar (optionale Parameter)
- **Primary Key**: `(client_name, client_id, return_type)` — drei Felder als Composite Key
- **OCR Grayscale**: Alle OCR-Aufrufe im Preprocessing müssen Grayscale-Konvertierung nutzen (vgl. debug_ocr.py Fix), da farbiger Text (z.B. blauer Fed EF Status) sonst nicht erkannt wird
- **Tabellengröße**: Bis zu 2000 Clients möglich (27 Rows/Seite = ~74 Scroll-Durchgänge). Fortschritts-Updates via message_queue essentiell.

## Confidence Score: 8/10

**One-pass implementation confidence** — likelihood that this plan can be executed successfully on the first attempt without additional research or clarification.

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 9 | Klare Patterns für GUI-Buttons, OCR-Scanning, Settings-Konfiguration, debug_ocr.py als Referenz |
| **External Knowledge** | 8 | CustomTkinter filedialog, CSV stdlib — gut dokumentiert, keine exotischen APIs |
| **Risk** | 7 | SSN/EIN-Koordinaten müssen kalibriert werden, aber debug_ocr.py ermöglicht schnelle Iteration |
| **Dependencies** | 6 | 6 Module betroffen, aber Änderungen sind backward-kompatibel via optionale Parameter |
| **Clarity** | 9 | Alle Anforderungen geklärt: Primary Key, Status-Werte, CSV-Format, GUI-Layout, Duplikat-Logik |
| **Testability** | 7 | Unit-Tests für CSV/State gut testbar, OCR braucht kalibrierte Koordinaten vom Remote-PC |

**Overall: 8/10** — Anforderungen vollständig geklärt, Screenshot bereitgestellt, debug_ocr.py als Kalibrierungs-Tool vorhanden. Einziger Unsicherheitsfaktor: SSN/EIN-Koordinaten müssen auf Remote-PC feinkalibriert werden.
