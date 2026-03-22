# Plan: Phase 10b-2 — CSV-Integration in Bot-Loop

> **Parent Plan**: `phase-10b-csv-integration-and-1040-fixes.md`
> **Sibling**: `phase-10b-1-1040-process-fixes.md` (should be completed FIRST)
> **Supersedes**: `phase-10b-csv-bot-integration.md` (OBSOLET)

## User Story

Als Steuerberater moechte ich, dass der Bot die CSV als persistentes Tracking nutzt: TODO-Clients werden bearbeitet, erfolgreiche als "Submitted" markiert, abgebrochene mit dem spezifischen FAIL-Grund, und wenn TaxAct einen neueren Status zeigt, wird die CSV automatisch aktualisiert.

## Acceptance Criteria

- [ ] Bot liest TODO-Clients aus CSV (gefiltert nach GUI Return Type)
- [ ] Erfolgreiche Clients: CSV Status = `Submitted`
- [ ] Abgebrochene Clients: CSV Status = `FAIL: <spezifischer Grund>` (aus abort_reason)
- [ ] Generische Fehler: CSV Status = `FAIL: <error_message>`
- [ ] ClientRow enthaelt `client_id` (SSN/EIN) fuer Composite-Key Lookup
- [ ] Auto-Update: Wenn TaxAct-Status neuer als CSV → CSV automatisch aktualisiert
- [ ] GUI: csv_path wird an BotController uebergeben
- [ ] GUI: CSV Status-Counts werden nach Bot-Run aktualisiert
- [ ] Backward-kompatibel: ohne CSV → altes in-memory Verhalten

## Context

Phase 10a hat die CSV-Infrastruktur (Preprocessing, Export, File-Picker, `update_client_status()`, `load_csv()`, `get_todo_clients()`) implementiert. Plan 10b-1 hat `abort_reason` im `ExecutionResult` eingefuehrt. Dieser Plan verbindet beides: der Bot-Loop nutzt die CSV fuer Client-Auswahl, schreibt Ergebnisse zurueck, und aktualisiert Status-Aenderungen aus TaxAct.

## Prerequisites

- **Phase 10a COMPLETE** — `preprocessor.py` mit CSV CRUD existiert
- **Plan 10b-1 COMPLETE** — `ExecutionResult.abort_reason` existiert

## Research Summary

### Relevant Files

| File | Purpose | Key Lines |
|------|---------|-----------|
| `clickbot/vision.py` | ClientRow, _scan_visible_clients, find_next_client | L618-625, L905-994, L997-1070 |
| `clickbot/bot_controller.py` | _run() main loop | L186-287 |
| `clickbot/gui.py` | _start_bot, _poll_messages | L715-735, L756-767 |
| `clickbot/preprocessor.py` | load_csv, update_client_status, ClientRecord | L236-298 (already implemented) |
| `clickbot/state.py` | ClientTracker (to be kept as fallback) | L1-57 |
| `config/settings.json` | SSN/EIN column config | L56 (ssn_ein: x=420, width=120) |

### Patterns to Follow

- **CSV CRUD**: `preprocessor.py:259-298` — `update_client_status()` reads CSV, finds by composite key, writes back
- **Column scanning**: `vision.py:678-731` — `get_column_positions(extra_columns=["ssn_ein"])` already supported
- **Cell reading**: `vision.py:793-829` — `_read_single_cell()` works for any column name
- **Optimized scan**: `vision.py:938-944` — reads fed_ef_status first (cheapest filter), then client_name

## Dependencies

- **New Packages**: none
- **Affected Modules**: `vision.py`, `bot_controller.py`, `gui.py`
- **Breaking Changes**: No — all new parameters have defaults for backward compatibility

## Tasks

### Task 1: UPDATE `clickbot/vision.py` — Add client_id to ClientRow

- **Action**: UPDATE
- **Implement**:
  1. Add `client_id: str = ""` field to `ClientRow` dataclass (L618-625), AFTER `client_name`
  2. Ensure all existing usages of `ClientRow` still work (default="" is backward-compatible)
- **Pattern**: Existing dataclass at vision.py:618-625
- **Depends on**: none
- **Validate**: `python -c "from clickbot.vision import ClientRow; r = ClientRow(0, 0, 'Test', '1040', ''); print(r.client_id); r2 = ClientRow(0, 0, 'Test', '1040', '', client_id='12-345'); print(r2.client_id)"`

### Task 2: UPDATE `clickbot/vision.py` — CSV-based client lookup in _scan_visible_clients

- **Action**: UPDATE
- **Implement**:
  1. Add parameter `csv_records: Optional[list] = None` to `_scan_visible_clients` (L905-910)
  2. At the top of the function: if `csv_records` is provided, build skip set:
     ```python
     if csv_records:
         skip_keys = {
             (r.client_name, r.client_id, r.return_type)
             for r in csv_records if r.status != "TODO"
         }
     ```
  3. After reading `client_name` for a candidate row (L953), also read `ssn_ein`:
     ```python
     ssn_ein = _read_single_cell("ssn_ein", row_y, column_positions, settings)
     ```
  4. Replace the `processed_clients` check (L963) with dual logic:
     ```python
     if csv_records:
         if (client_name, ssn_ein, selected_return_type) in skip_keys:
             logger.debug(f"Row {row_index}: {client_name} not TODO in CSV, skipping")
             continue
     elif processed_clients and client_name in processed_clients:
         logger.debug(f"Row {row_index}: {client_name} already processed, skipping")
         continue
     ```
  5. Include `client_id=ssn_ein` in the returned `ClientRow` (L982-988)
  6. Keep `processed_clients` parameter for backward compatibility
- **Pattern**: Existing check at vision.py:963, `_read_single_cell` at vision.py:793
- **Depends on**: Task 1
- **Validate**: Code review — `csv_records` parameter accepted, SSN/EIN read for candidates

### Task 3: UPDATE `clickbot/vision.py` — Update find_next_client for CSV + auto-status-update

- **Action**: UPDATE
- **Implement**:
  1. Add parameter `csv_records: Optional[list] = None` to `find_next_client` (L997-1001)
  2. If `csv_records` provided: call `get_column_positions(extra_columns=["ssn_ein"])` instead of `get_column_positions()` (L1026)
  3. Pass `csv_records` through to `_scan_visible_clients` (L1042-1044)
  4. Add `status_updates` list to collect auto-updates:
     ```python
     status_updates = []
     ```
  5. In `_scan_visible_clients`: for rows with non-empty fed_ef_status AND csv_records provided:
     - Read `ssn_ein` and `return_type` (via `_read_single_cell`)
     - Build key `(client_name, ssn_ein, normalized_return_type)`
     - Look up in csv_records: if CSV status differs from TaxAct fed_ef_status → add to `status_updates`
  6. Change `find_next_client` return signature to include status_updates:
     - When csv_records provided: return `(ClientRow, click_pos, status_updates)` or `(None, status_updates)`
     - When csv_records is None: return existing format `(ClientRow, click_pos)` or `None`

  **IMPORTANT**: The return type changes when csv_records is used. The caller (bot_controller._run) must handle both cases.
- **Pattern**: `_scan_visible_clients` return format at vision.py:991-994, `normalize_return_type` at vision.py:638-675
- **Depends on**: Task 2
- **Validate**: `python -c "from clickbot.vision import find_next_client; import inspect; sig = inspect.signature(find_next_client); assert 'csv_records' in sig.parameters; print('OK')"`

### Task 4: UPDATE `clickbot/bot_controller.py` — Add csv_path + CSV tracking in _run()

- **Action**: UPDATE
- **Implement**:
  1. Add `csv_path: Optional[Path] = None` parameter to `BotController.__init__` (L48), import Path
  2. Store as `self.csv_path = csv_path`
  3. Refactor `_run()` (L186-287):

  **At start of _run (after L208):**
  ```python
  from clickbot.preprocessor import load_csv, update_client_status

  csv_records = None
  if self.csv_path and self.csv_path.exists():
      csv_records = load_csv(self.csv_path)
      todo_count = sum(
          1 for r in csv_records
          if r.return_type == self.selected_return_type and r.status == "TODO"
      )
      self._send_log(f"CSV loaded: {todo_count} TODO clients for {self.selected_return_type}")
  ```

  **Replace find_next_client call (L224-228):**
  ```python
  if csv_records:
      find_result = vision.find_next_client(
          self.settings,
          selected_return_type=self.selected_return_type,
          csv_records=csv_records
      )
      if find_result is None:
          # No more clients
          client_result = None
          status_updates = []
      elif find_result[0] is None:
          client_result = None
          status_updates = find_result[1]
      else:
          client_result = (find_result[0], find_result[1])
          status_updates = find_result[2]

      # Process auto-status-updates
      for name, cid, rtype, new_status in status_updates:
          update_client_status(self.csv_path, name, cid, rtype, new_status)
          self._send_log(f"Status updated: {name} -> {new_status}")
      if status_updates:
          csv_records = load_csv(self.csv_path)
  else:
      client_result = vision.find_next_client(
          self.settings,
          selected_return_type=self.selected_return_type,
          processed_clients=tracker.processed
      )
  ```

  **After process execution (L276-284):**
  ```python
  if result.success:
      if self.csv_path:
          update_client_status(
              self.csv_path, client_row.client_name,
              client_row.client_id, self.selected_return_type, "Submitted"
          )
          csv_records = load_csv(self.csv_path)
      self._send_log(f"Completed: {client_row.client_name}")
  else:
      if result.error_message == "Stopped by user":
          break
      # Determine CSV status
      if self.csv_path:
          if result.abort_reason:
              csv_status = result.abort_reason
          else:
              csv_status = f"FAIL: {result.error_message or 'Unknown error'}"
          update_client_status(
              self.csv_path, client_row.client_name,
              client_row.client_id, self.selected_return_type, csv_status
          )
          csv_records = load_csv(self.csv_path)
      self._send_log(f"SKIPPED: {client_row.client_name} - {result.abort_reason or result.error_message}")
      sounds.play_error()
      self._recover_to_client_manager()
  ```

  4. Keep `ClientTracker` as fallback when `csv_path is None`
  5. Remove `tracker.mark_processed()` when using CSV path (CSV is the source of truth)
- **Pattern**: Existing _run() loop at bot_controller.py:186-287
- **Depends on**: Tasks 1-3, Plan 10b-1 (abort_reason in ExecutionResult)
- **Validate**: `python -c "from clickbot.bot_controller import BotController; import inspect; sig = inspect.signature(BotController.__init__); assert 'csv_path' in sig.parameters; print('OK')"`

### Task 5: UPDATE `clickbot/gui.py` — Pass csv_path + refresh after bot run

- **Action**: UPDATE
- **Implement**:
  1. In `_start_bot` (L718): pass `csv_path=self._csv_path` to BotController:
     ```python
     self.controller = BotController(
         self.settings,
         selected_return_type=selected_return_type,
         csv_path=self._csv_path
     )
     ```
  2. In `_poll_messages` (L756-767): when bot state becomes IDLE, reload CSV to refresh counts:
     ```python
     if self.controller.get_state() == BotState.IDLE:
         if self._csv_path:
             self._load_csv_file(self._csv_path)
         self._set_ready_state()
     ```
- **Pattern**: `_load_csv_file` already refreshes counts (gui.py:569-599)
- **Depends on**: Task 4
- **Validate**: Code review — BotController receives csv_path, GUI refreshes after run

### Task 6: ADD Unit Tests for CSV Integration

- **Action**: ADD
- **Implement**: Create/update tests in `tests/unit/`:
  1. **test_vision.py**:
     - Test `ClientRow` with `client_id` field (default="" and explicit value)
     - Test `find_next_client` accepts `csv_records` parameter
  2. **test_bot_controller.py**:
     - Test `BotController.__init__` accepts `csv_path`
     - Test `_run()` with csv_path loads CSV and filters TODO clients (mocked vision)
     - Test successful processing writes "Submitted" to CSV (mocked)
     - Test failed processing writes "FAIL: <reason>" to CSV (mocked)
  3. **test_csv_integration.py** (new file):
     - Test end-to-end: create temp CSV, simulate bot run, verify status updates
     - Test auto-status-update: CSV has "Submitted", TaxAct shows "Ext. Accepted" → CSV updated
     - Test backward compat: csv_path=None → uses in-memory Set, no CSV changes
     - Edge case: all clients DONE → bot reports "All done!"
     - Edge case: client not found in CSV → warning logged, no crash
- **Pattern**: Existing test patterns with mocked pyautogui/vision, temp files via `tmp_path`
- **Depends on**: Tasks 1-5
- **Validate**: `pytest tests/unit/ -v`

## Testing Requirements

- [ ] CSV loaded at bot start, TODO count logged
- [ ] Successful client → CSV status = "Submitted"
- [ ] Aborted client (abort_reason) → CSV status = exact abort_reason string
- [ ] Generic error → CSV status = "FAIL: <error_message>"
- [ ] Auto-update: TaxAct status differs from CSV → CSV updated during scan
- [ ] GUI refreshes CSV counts after bot finishes
- [ ] Backward compat: csv_path=None → in-memory tracking, no CSV touched
- [ ] Edge case: empty CSV (no TODO clients) → "All done!" immediately
- [ ] Edge case: SSN/EIN column not found → graceful fallback or clear error

**Test Levels**: Unit + Integration

## Bug Handling

- Bugs caused by THESE changes → Fix immediately
- Pre-existing bugs → Document in `.agents/bugs/`, do NOT fix
- NEVER modify 1040.json, 1120.json, or 1120S.json in this plan

## Rollback Strategy

1. `git stash` or `git checkout .` to revert changes
2. `state.py` is NOT modified — remains as fallback
3. `csv_path=None` default → all modules revert to old behavior
4. CSV files in `C:\TaxActBot\logs\` are not corrupted (worst case: extra status entries)

## Manual Verification

- [ ] Bot starts with CSV, log shows "CSV loaded: X TODO clients for 1040"
- [ ] Processing 1040 client → CSV updated to "Submitted", GUI counts refresh
- [ ] Processing fails (wizard) → CSV updated to "FAIL: Wizard (Stage 12)"
- [ ] Client with "Submitted" in CSV but "Ext. Accepted" in TaxAct → CSV auto-updated
- [ ] Bot-Restart: CSV reloaded, previously Submitted clients skipped
- [ ] 1120S bot run: still works with CSV (different return type filter)
- [ ] No CSV loaded → "ERROR: No CSV file loaded" message (already implemented in GUI)

## Notes

- `update_client_status` in preprocessor.py rewrites the entire CSV on each call. For large client lists (500+), consider caching in-memory and writing periodically. For now, per-iteration writes are acceptable.
- The auto-status-update adds 2 extra OCR calls (ssn_ein + return_type) per skipped row during scanning. If performance is an issue, it can be disabled by not passing csv_records.
- `state.py` is NOT deleted or modified. It stays as fallback and can be removed in a future cleanup.
- The `find_next_client` return signature changes when `csv_records` is provided (includes status_updates). This is the most complex part of the plan — careful implementation needed.

## Confidence Score: 8/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 9/10 | CSV CRUD, column scanning, cell reading all exist |
| **External Knowledge** | 10/10 | Pure Python, no external APIs |
| **Risk** | 7/10 | find_next_client return signature change is complex; auto-update adds OCR overhead |
| **Dependencies** | 7/10 | 3 files + depends on Plan 10b-1 being complete |
| **Clarity** | 8/10 | Core flow clear, auto-update edge cases need attention |
| **Testability** | 8/10 | CSV logic fully testable via temp files, E2E needs TaxAct |

**Overall: 8/10** — CSV infrastructure already exists (preprocessor.py), clear patterns to follow. Main risk is the find_next_client return signature change and auto-update OCR overhead.
