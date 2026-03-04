# Plan: GUI Return-Type-Auswahl

## User Story

Als Steuerberater möchte ich in der GUI den Return-Type (1120, 1120S, 1040) auswählen können, damit der Bot keine OCR-Erkennung des Return-Types mehr benötigt und zuverlässiger läuft.

## Acceptance Criteria

- [ ] GUI zeigt einen Segmented-Button mit Optionen: "1120" | "1120S" | "1040"
- [ ] Der Bot verwendet den GUI-gewählten Return-Type für alle Clients (keine OCR-Erkennung)
- [ ] Der Selector ist während Countdown und Running deaktiviert
- [ ] Der Bot liest weiterhin `client_name` und `fed_ef_status` via OCR (unverändert)
- [ ] Der Bot liest `return_type` NICHT mehr via OCR aus der Tabelle
- [ ] Alle bestehenden Tests bestehen weiterhin

## Context

Bisher erkennt der Bot den Return-Type jedes Clients automatisch via OCR aus der Tabellenspalte. Dies soll durch eine manuelle GUI-Auswahl ersetzt werden — der Benutzer stellt den Typ vor dem Start ein. Die OCR-Scan-Logik für die Spalte `return_type` entfällt komplett, was den Scan schneller und robuster macht.

## Research Summary

### Relevant Files

| File | Purpose | Relevante Zeilen |
|------|---------|-------|
| `clickbot/gui.py` | GUI-Widgets, Start-Logik, BotController-Erstellung | 81–101, 269–287 |
| `clickbot/bot_controller.py` | `__init__`, `start()`, `_run()` Loop | 46–57, 196–263 |
| `clickbot/vision.py` | `get_column_positions()`, `_scan_visible_clients()`, `find_next_client()` | 627–665, 761–858, 861–934 |
| `clickbot/vision.py` | `ClientRow` Dataclass | 573–580 |

### Patterns to Follow

- **CTkSegmentedButton** bereits via `import customtkinter as ctk` verfügbar — kein neues Package
- `BotController(self.settings)` in `gui.py:271` → wird erweitert zu `BotController(self.settings, selected_return_type=...)`
- `_scan_visible_clients()` in `vision.py:761` folgt dem Pattern: optionale Parameter mit Default → weiterhin beibehalten
- Andere Parameter-Übergaben in `_run()` als Vorlage: `vision.configure(self.settings)` zeigt wie Settings weitergegeben werden

## Dependencies

- **New Packages**: keine
- **Affected Modules**: `gui.py`, `bot_controller.py`, `vision.py`
- **Breaking Changes**: Nein — `find_next_client()` Signatur ändert sich (neuer Parameter), aber nur intern aufgerufen

## Tasks

### Task 1: ADD Return-Type-Selector in `clickbot/gui.py`

- **Action**: UPDATE
- **Implement**:
  1. In `_create_widgets()` nach `self.control_frame`-Block: neues `self.return_type_frame = ctk.CTkFrame(self)` + Label `"Return Type:"` + `self.return_type_selector = ctk.CTkSegmentedButton(...)` mit Werten `["1120", "1120S", "1040"]` und Default `"1120S"`
  2. In `_setup_layout()`: `self.return_type_frame` als neue `row=1` einfügen; alle nachfolgenden Frames (`control_frame`, `status_frame`, `log_frame`) um 1 hochzählen (row 2, 3, 4). Grid-Weight-Konfiguration in `_setup_window()` anpassen: `self.grid_rowconfigure(4, weight=1)` statt `row=3`
  3. Fensterhöhe in `settings.json` von 600 → 650 anpassen
  4. In `_set_ready_state()`: `self.return_type_selector.configure(state="normal")`
  5. In `_start_countdown()`: `self.return_type_selector.configure(state="disabled")`
  6. In `_start_bot()`: `BotController(self.settings, selected_return_type=self.return_type_selector.get())`
- **Pattern**: Bestehende Widget-Erstellung in `gui.py:81–144`; Grid-Layout in `gui.py:146–168`
- **Depends on**: none
- **Validate**: `python -c "from clickbot.gui import BotGUI; print('OK')"`

### Task 2: UPDATE `BotController.__init__()` in `clickbot/bot_controller.py`

- **Action**: UPDATE
- **Implement**:
  1. `__init__(self, settings: dict, selected_return_type: str = "1120S")` — neuer Parameter mit sinnvollem Default
  2. `self.selected_return_type = selected_return_type` als Instanzvariable speichern
- **Pattern**: Bestehende `__init__` in `bot_controller.py:46–57`
- **Depends on**: Task 1 (GUI muss den Wert übergeben)
- **Validate**: `python -c "from clickbot.bot_controller import BotController; print('OK')"`

### Task 3: UPDATE `_run()` in `clickbot/bot_controller.py`

- **Action**: UPDATE
- **Implement**:
  1. `vision.find_next_client()` Aufruf in Zeile ~201 erweitern: `selected_return_type=self.selected_return_type` übergeben
  2. `process_executor.execute(client_row.return_type)` in Zeile ~250 ändern zu `process_executor.execute(self.selected_return_type)` — **kritisch**: `client_row.return_type` wäre nach der vision.py-Änderung ohnehin der selected_return_type, aber zur Klarheit direkt `self.selected_return_type` verwenden
  3. Log-Zeile `f"Selected: {client_row.client_name} ({client_row.return_type})"` bleibt korrekt da `client_row.return_type` ab Task 4 = `selected_return_type`
- **Pattern**: Bestehender `_run()` Aufruf in `bot_controller.py:201`, `bot_controller.py:250`
- **Depends on**: Task 2
- **Validate**: `python -c "from clickbot.bot_controller import BotController; b = BotController({'dev_mode': False}, '1120S'); print(b.selected_return_type)"`

### Task 4: UPDATE `get_column_positions()` in `clickbot/vision.py`

- **Action**: UPDATE
- **Implement**:
  1. `header_templates` Dict in Zeile ~640 den Eintrag `"return_type": "common/column_header_return_type.png"` entfernen
  2. Damit sucht `get_column_positions()` nur noch 2 Header: `client_name` und `fed_ef_status`
  3. Log-Zeile am Ende entsprechend korrekt (zeigt automatisch die gefundenen Keys)
- **Pattern**: Bestehende `get_column_positions()` in `vision.py:627–665`
- **Depends on**: none (unabhängig von Task 1–3)
- **Validate**: `python -c "from clickbot.vision import get_column_positions; print('OK')"`

### Task 5: UPDATE `_scan_visible_clients()` in `clickbot/vision.py`

- **Action**: UPDATE
- **Implement**:
  1. Signatur erweitern: `selected_return_type: str` als neuen Parameter (non-optional)
  2. **Schritt 3 komplett entfernen** (Zeilen ~823–836):
     - `raw_return_type = _read_single_cell("return_type", ...)` — entfernen
     - `return_type = normalize_return_type(raw_return_type)` — entfernen
     - `is_valid_type = return_type in ("1120", "1120S")` — entfernen
     - `if not is_valid_type: continue` — entfernen
     - `if target_return_type: type_matches = ...` — entfernen
     - `if type_matches:` → ersetzen durch direktes `if True:` bzw. Block einrücken ohne Bedingung
  3. Im `ClientRow(...)` Konstruktor: `return_type=selected_return_type` (war vorher das OCR-Ergebnis)
  4. Den `target_return_type` Parameter entfernen, `selected_return_type: str` stattdessen
  5. Debug-Log aktualisieren: `f"Row {row_index}: name='{client_name}', type='{selected_return_type}', status_empty=True"`
- **Pattern**: Bestehende `_scan_visible_clients()` in `vision.py:761–858`
- **Depends on**: Task 4
- **Validate**: `python -c "from clickbot.vision import _scan_visible_clients; print('OK')"`

### Task 6: UPDATE `find_next_client()` in `clickbot/vision.py`

- **Action**: UPDATE
- **Implement**:
  1. Signatur: `target_return_type: Optional[str] = None` entfernen, `selected_return_type: str` hinzufügen
  2. Aufruf von `_scan_visible_clients(...)` in Zeile ~906: `target_return_type` → `selected_return_type=selected_return_type`
  3. Docstring aktualisieren: "Return Type matches target_return_type" Zeile entfernen, stattdessen "Return Type is set from selected_return_type (user selection)"
- **Pattern**: Bestehende `find_next_client()` in `vision.py:861–934`
- **Depends on**: Task 5
- **Validate**: `python -c "from clickbot.vision import find_next_client; print('OK')"`

### Task 7: UPDATE `settings.json`

- **Action**: UPDATE
- **Implement**:
  1. `gui.window_height`: `600` → `650`
- **Pattern**: Bestehende settings in `config/settings.json:43–48`
- **Depends on**: Task 1 (GUI braucht mehr Platz)
- **Validate**: `python -c "import json; s=json.load(open('config/settings.json')); print(s['gui']['window_height'])"`

### Task 8: UPDATE Unit Tests für `vision.py`

- **Action**: UPDATE
- **Implement**:
  1. Alle Test-Aufrufe von `find_next_client(settings, ...)` → `find_next_client(settings, selected_return_type="1120S", ...)`
  2. Alle Test-Aufrufe von `_scan_visible_clients(settings, col_pos, ...)` → `selected_return_type="1120"` hinzufügen
  3. Tests die `return_type` in `ClientRow` per OCR-Ergebnis prüfen → anpassen auf übergebenen Wert
  4. Tests für `get_column_positions()` prüfen ob `"return_type"` Key — anpassen (Key existiert nicht mehr)
- **Pattern**: Bestehende Tests in `tests/unit/test_vision.py`
- **Depends on**: Tasks 4–6
- **Validate**: `pytest tests/unit/test_vision.py -v`

### Task 9: RUN full test suite

- **Action**: keine Code-Änderung
- **Implement**: Test-Suite ausführen und alle Fehler beheben
- **Depends on**: Tasks 1–8
- **Validate**: `pytest tests/unit -v`

## Testing Requirements

- [ ] `BotController("1120")` und `BotController("1040")` instanziierbar
- [ ] `find_next_client(settings, selected_return_type="1120S", ...)` funktioniert ohne `return_type`-Spalte
- [ ] `_scan_visible_clients()` setzt `ClientRow.return_type` korrekt aus Parameter (nicht OCR)
- [ ] `get_column_positions()` sucht nur noch 2 Header (kein `return_type`)
- [ ] GUI: Selector startet mit Default "1120S"
- [ ] Edge case: Selector disabled während Running, enabled nach Stop
- [ ] Edge case: `find_next_client` mit leerem `processed_clients` funktioniert wie bisher

**Test Levels**: Unit (Tasks 4–6, 8), Manuell (Tasks 1, 7)

## Bug Handling

- Bugs durch diese Änderungen → sofort fixen
- Pre-existing Bugs → in `.agents/bugs/` dokumentieren, NICHT fixen
- NIEMALS Code außerhalb des Scopes ändern

## Rollback Strategy

1. `git stash` oder `git checkout -- clickbot/gui.py clickbot/bot_controller.py clickbot/vision.py config/settings.json`
2. Tests nochmals ausführen: `pytest tests/unit -v`

## Manual Verification

Nach Implementierung manuell prüfen:

- [ ] GUI öffnet sich mit Segmented-Button (1120 | 1120S | 1040), Default = "1120S"
- [ ] Selector ist grayed out während Countdown und während der Bot läuft
- [ ] Nach Stop wird Selector wieder aktiv
- [ ] Bot startet korrekt mit dem gewählten Return-Type (Log zeigt richtigen Type)
- [ ] Bot überspringt Clients mit gefülltem Fed EF Status korrekt (OCR für fed_ef_status läuft noch)

## Notes

- `normalize_return_type()` und die `_RETURN_TYPE_PATTERN` Regex in `vision.py` können technisch bleiben — sie werden im neuen Flow nicht mehr aufgerufen, aber als Utility für zukünftige Zwecke oder Tests nicht entfernen
- `column_header_return_type.png` Asset bleibt im Dateisystem — kein Aufräumen nötig
- Der `1040`-Prozess (Plan B) benötigt nur eine neue `config/processes/1040.json` — `process_loader.py` lädt bereits jede `{return_type}.json` generisch
