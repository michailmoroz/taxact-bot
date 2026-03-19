# Plan: Phase 10b — CSV-Integration in Bot-Loop

## User Story

Als Steuerberater möchte ich, dass der Bot die Preprocessing-CSV als Basis für das Client-Tracking nutzt und nach jeder Iteration den Status (DONE/FAIL) persistent in der CSV aktualisiert, damit kein Client doppelt bearbeitet wird und der Fortschritt über Neustarts erhalten bleibt.

## Acceptance Criteria

- [ ] Bot-Start nur möglich wenn CSV geladen — sonst Fehlermeldung
- [ ] Bot liest TODO-Clients aus CSV (gefiltert nach gewähltem Return Type)
- [ ] Nach erfolgreicher Iteration: Client in CSV als `DONE` markiert
- [ ] Nach fehlgeschlagener Iteration: Client in CSV als `FAIL` markiert
- [ ] Wenn Client+ID+Return Type als DONE → auch TaxAct-Duplikate werden übersprungen
- [ ] `find_next_client()` nutzt CSV-Daten statt in-memory Set
- [ ] `ClientRow` enthält `client_id` (SSN/EIN) Feld
- [ ] Bestehende 1120S/1120/1040-Prozesse weiterhin funktionsfähig

## Context

Phase 10b baut auf Phase 10a auf. Das Preprocessing und die CSV-Infrastruktur existieren bereits. Jetzt wird der Bot-Loop umgebaut: `state.py` wechselt von in-memory Set auf CSV-basiertes Tracking, `bot_controller.py` nutzt die CSV für Client-Auswahl und Status-Updates, und `vision.py:find_next_client()` matcht Clients per (Name, ID, Return Type) statt nur per Name.

## Prerequisites

- **Phase 10a muss COMPLETE sein** — `preprocessor.py`, GUI File-Picker, CSV-Export funktionieren
- CSV-Datei mit korrekten Daten muss vorhanden sein

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `clickbot/state.py` | In-memory ClientTracker | L1-57 (gesamte Datei) |
| `clickbot/bot_controller.py` | Main Loop, `_run()` | L186-287 |
| `clickbot/vision.py` | `find_next_client()`, `_scan_visible_clients()`, `ClientRow` | L618-971 |
| `clickbot/gui.py` | `_start_bot()` übergibt csv_path | Phase 10a erweitert |
| `clickbot/preprocessor.py` | `load_csv()`, `update_client_status()`, `ClientRecord` | Phase 10a erstellt |

### Patterns to Follow
- **State Tracking**: `state.py:15-57` — ClientTracker mit `mark_processed()`, `is_processed()`
- **Bot Loop**: `bot_controller.py:212-287` — find_next_client → mark_processed → execute → handle result
- **Table Scanning**: `vision.py:806-895` — `_scan_visible_clients()` mit optimierter Read-Order

## Dependencies

- **New Packages**: none
- **Affected Modules**: `state.py`, `bot_controller.py`, `vision.py`, `gui.py`
- **Breaking Changes**: Ja — `state.py` Interface ändert sich (aber backward-kompatibel via optionale Parameter)

## Tasks

### Task 1: REFACTOR `clickbot/state.py` — CSV-basiertes Tracking

- **Action**: REFACTOR
- **Implement**: `ClientTracker` erweitern:
  1. Neuer Constructor-Parameter: `csv_path: Optional[Path] = None`
  2. `load_from_csv(csv_path)` — liest CSV via `preprocessor.load_csv()`, baut Lookup-Dict `{(name, id, return_type): status}`
  3. `is_processed(client_name, client_id="", return_type="")` — wenn csv_path gesetzt: prüft `(name, id, return_type)` Status != `TODO`. Wenn csv_path=None: altes Verhalten (prüft `client_name in self.processed`)
  4. `mark_done(client_name, client_id, return_type)` — setzt Status `DONE` in-memory + schreibt CSV via `preprocessor.update_client_status()`
  5. `mark_failed(client_name, client_id, return_type)` — setzt Status `FAIL` in-memory + schreibt CSV
  6. `get_todo_clients(return_type)` — gibt TODO-Clients für Return Type zurück
  7. Backward-Kompatibilität: `mark_processed(client_name)` bleibt für altes Interface, `csv_path=None` = altes Verhalten

- **Pattern**: `state.py:1-57`
- **Depends on**: Phase 10a (preprocessor.py existiert)
- **Validate**: `python -c "from clickbot.state import ClientTracker; t = ClientTracker(); t.mark_processed('test'); assert t.is_processed('test'); print('OK')"`

### Task 2: UPDATE `clickbot/vision.py` — ClientRow + find_next_client CSV-Support

- **Action**: UPDATE
- **Implement**:
  1. `ClientRow` Dataclass erweitern: `client_id: str = ""` (backward-kompatibel mit Default)
  2. `_scan_visible_clients()` anpassen:
     - Neuer Parameter: `todo_clients: Optional[List[ClientRecord]] = None`
     - Wenn `todo_clients` gegeben:
       - OCR liest auch `ssn_ein` Spalte (via `_read_single_cell("ssn_ein", ...)`)
       - Matching: `(client_name, client_id, return_type)` muss in todo_clients sein UND `fed_ef_status` leer
       - `ClientRow.client_id` wird gesetzt
     - Wenn `todo_clients=None`: altes Verhalten (processed_clients Set)
  3. `find_next_client()` anpassen:
     - Neuer Parameter: `todo_clients: Optional[List[ClientRecord]] = None`
     - Durchgereicht an `_scan_visible_clients()`
     - `get_column_positions()` mit `extra_columns=["ssn_ein"]` wenn todo_clients gegeben

- **Pattern**: `vision.py:806-895` (`_scan_visible_clients`), `vision.py:898-971` (`find_next_client`)
- **WICHTIG — Return-Signatur beachten**: `_scan_visible_clients()` gibt aktuell ein **3-Tuple** zurück: `(ClientRow|None, click_pos|None, last_client_name: str)`. `find_next_client()` entpackt dieses 3-Tuple in `row_data, click_pos, current_last_client`. Die Erweiterung um `todo_clients` muss dieses Format **exakt beibehalten** — sowohl die Aufrufe in `find_next_client()` (L949-953) als auch der Rückgabewert von `_scan_visible_clients()` (L898 + L901).
- **Depends on**: Task 1
- **Validate**: `python -c "from clickbot.vision import ClientRow; r = ClientRow(0, 0, 'test', '1120S', '', client_id='12-345'); print(r.client_id)"`

### Task 3: UPDATE `clickbot/bot_controller.py` — CSV im Loop nutzen

- **Action**: UPDATE
- **Implement**:
  1. Constructor: Neuer Parameter `csv_path: Optional[Path] = None`
  2. `_run()` anpassen:
     - `ClientTracker(csv_path=self.csv_path)` statt `ClientTracker()`
     - Wenn csv_path: `tracker.load_from_csv()` vor Loop-Start
     - Wenn csv_path: `todo_clients = tracker.get_todo_clients(self.selected_return_type)` vor Loop
     - `find_next_client()` mit `todo_clients=todo_clients` aufrufen
     - Nach Erfolg: `tracker.mark_done(client_row.client_name, client_row.client_id, client_row.return_type)`
     - Nach Fehler: `tracker.mark_failed(client_row.client_name, client_row.client_id, client_row.return_type)`
     - Alte `tracker.mark_processed(client_row.client_name)` entfernen wenn csv_path gesetzt
  3. Ohne csv_path: altes Verhalten beibehalten (Fallback)

- **Pattern**: `bot_controller.py:186-287`
- **Depends on**: Task 1, Task 2
- **Validate**: `python -c "from clickbot.bot_controller import BotController; print('OK')"`

### Task 4: UPDATE `clickbot/gui.py` — csv_path an BotController übergeben

- **Action**: UPDATE
- **Implement**:
  1. `_on_start_click()`: Wenn `self._csv_path is None` → `_log("ERROR: No CSV file loaded. Run Preprocessing or load a CSV file.")` + return
  2. `_start_bot()`: `BotController(self.settings, selected_return_type=..., csv_path=self._csv_path)`

- **Pattern**: `gui.py:394-414` (`_start_bot`)
- **Depends on**: Task 3
- **Validate**: Manuell — Bot starten mit geladener CSV, Status-Updates prüfen

## Testing Requirements

- [ ] Unit: `state.py` — CSV-basiertes `is_processed()` mit (Name, ID, Return Type)
- [ ] Unit: `state.py` — `mark_done` / `mark_failed` schreiben CSV korrekt
- [ ] Unit: `state.py` — Backward-Kompatibilität ohne csv_path (altes Set-Verhalten)
- [ ] Unit: `vision.py` — `ClientRow` mit `client_id` Default=""
- [ ] Integration: CSV laden → Bot starten → Client bearbeiten → CSV Status = DONE
- [ ] Integration: CSV laden → Bot Fehler → CSV Status = FAIL
- [ ] Edge case: Alle Clients in CSV bereits DONE → Bot meldet "All done!"
- [ ] Edge case: Duplikate in TaxAct → nur einer wird bearbeitet (der andere übersprungen)

**Test Levels**: Unit + Integration + E2E

## Bug Handling

- Bugs caused by THESE changes → Fix immediately
- Pre-existing bugs → Document in `.agents/bugs/`, do NOT fix

## Rollback Strategy

1. `git stash` or `git checkout .` to revert
2. `state.py` Fallback: `csv_path=None` → altes in-memory Set Verhalten
3. `vision.py` `ClientRow.client_id` hat Default "" → alte Aufrufe brechen nicht
4. `bot_controller.py` `csv_path=None` → altes Verhalten

## Manual Verification

- [ ] Bot-Start ohne CSV: Fehlermeldung
- [ ] Bot-Start mit CSV: Verarbeitet nur TODO-Clients des gewählten Return Types
- [ ] Nach erfolgreicher Iteration: CSV zeigt DONE für diesen Client
- [ ] Nach Fehler: CSV zeigt FAIL für diesen Client
- [ ] Duplikate: Zweites Vorkommen in TaxAct wird übersprungen
- [ ] Neustart: CSV laden → DONE-Clients werden übersprungen

## Notes

- Phase 10b setzt Phase 10a voraus — alle Preprocessing-Infrastruktur muss funktionieren
- Backward-Kompatibilität ist über optionale Parameter gewährleistet
- Bei csv_path=None verhält sich alles wie vorher (für Tests oder Notfall-Fallback)

## Confidence Score: 9/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 9 | Bestehender Bot-Loop als klare Vorlage |
| **External Knowledge** | 10 | Nur interne Module, keine externen APIs |
| **Risk** | 8 | state.py Refactoring mit Backward-Kompatibilität, find_next_client Erweiterung |
| **Dependencies** | 8 | 4 Module, aber klare Abhängigkeitskette (state → vision → bot_controller → gui) |
| **Clarity** | 10 | Alle Anforderungen aus Phase 10a-Kontext klar |
| **Testability** | 8 | CSV-Logik voll testbar, E2E braucht TaxAct |

**Overall: 9/10** — Klare Abhängigkeitskette, Backward-Kompatibilität via Defaults, Phase 10a als solide Basis.
