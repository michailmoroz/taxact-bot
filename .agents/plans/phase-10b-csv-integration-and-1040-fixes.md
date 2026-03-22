# Plan: Phase 10b — CSV-Integration in Bot-Loop + 1040 Process Fixes

## User Story

Als Steuerberater moechte ich, dass der Bot nach jeder Client-Bearbeitung den Status (Submitted/FAIL mit Grund) in der CSV aktualisiert und gesperrte Clients korrekt handhabt, damit ich den Fortschritt persistent verfolgen kann und der Bot zuverlaessiger arbeitet.

## Acceptance Criteria

- [ ] Bot verwendet CSV fuer Client-Tracking statt in-memory Set
- [ ] Erfolgreiche Clients erhalten Status `Submitted` in CSV
- [ ] Abgebrochene Clients erhalten spezifischen FAIL-Status (z.B. `FAIL: Alerts not passed`)
- [ ] Locked Clients werden korrekt gehandhabt (locked_1 Dialog + locked_2 Popup)
- [ ] Stage 12 Wizard-Erkennung funktioniert zuverlaessig (search_region fuer no_default.png)
- [ ] Stage 16 und 18 brechen sauber ab mit `abort: true`
- [ ] Auto-Status-Update: CSV wird aktualisiert wenn TaxAct neueren Status zeigt
- [ ] Backward-kompatibel: 1120/1120S Prozesse weiterhin funktionsfaehig

## Context

Phase 10a hat die CSV-Infrastruktur (Preprocessing, Export, File-Picker) implementiert. Phase 10b integriert die CSV in den Bot-Loop: der Bot liest TODO-Clients aus der CSV, verarbeitet sie, und schreibt Ergebnisse (Submitted/FAIL) zurueck. Gleichzeitig werden 1040-spezifische Prozessfixes eingebaut (Wizard-Handling, Locked Clients, saubere Aborts).

## Research Summary

### Relevant Files

| File | Purpose | Lines |
|------|---------|-------|
| `clickbot/process_executor.py` | ExecutionResult + abort handling | L27-34 (dataclass), L141-153 (error path), L242-263 (_action_click), L413-441 (_execute_branch abort) |
| `clickbot/bot_controller.py` | Main loop + CSV integration point | L48-62 (init), L186-287 (_run), L244-259 (double-click + execute) |
| `clickbot/vision.py` | ClientRow + table scan | L618-625 (ClientRow), L905-994 (_scan_visible_clients), L997-1070 (find_next_client) |
| `clickbot/gui.py` | CSV path pass-through | L615-627 (_on_start_click), L715-735 (_start_bot) |
| `clickbot/preprocessor.py` | CSV read/write (already implemented) | L259-298 (update_client_status), L301-317 (get_todo_clients) |
| `clickbot/state.py` | In-memory tracker (to be replaced) | Full file |
| `config/processes/1040.json` | 1040 process stages | Stages 3, 12, 16, 18 |
| `config/settings.json` | SSN/EIN column config already present | L56 (ssn_ein: x=420, width=120) |

### Patterns to Follow

- **Abort branches**: Stage 12 in `1040.json:133-156` already uses `"abort": true` pattern — replicate for Stages 16/18
- **Conditional in multi**: `_action_multi` (process_executor.py:733) calls `_execute_step` per sub-action, which routes to `_action_conditional` — nesting works
- **CSV functions**: `preprocessor.py:259-298` already has `update_client_status()` with composite key lookup
- **Extra columns**: `vision.py:678-731` `get_column_positions(extra_columns=["ssn_ein"])` already supported

## Dependencies

- **New Packages**: none
- **Affected Modules**: process_executor.py, bot_controller.py, vision.py, gui.py, state.py, 1040.json
- **Breaking Changes**: No — `find_next_client()` keeps backward-compatible signature with defaults

## Tasks

### Task 1: UPDATE `clickbot/process_executor.py` — Add abort_reason support

- **Action**: UPDATE
- **Implement**:
  1. Add `abort_reason: Optional[str] = None` field to `ExecutionResult` (L27-34)
  2. Add `self._last_abort_reason: Optional[str] = None` to `__init__` (L47-69)
  3. In `_execute_branch` (L432-441): when `branch.get("abort")`, read `branch.get("abort_reason")` and store on `self._last_abort_reason`
  4. In `execute()` error path (L141-153): include `abort_reason=self._last_abort_reason` in ExecutionResult
  5. Reset `self._last_abort_reason = None` at start of each `execute()` call
- **Pattern**: Follows existing `error_message`/`error_step` pattern in ExecutionResult
- **Depends on**: none
- **Validate**: `python -c "from clickbot.process_executor import ExecutionResult; r = ExecutionResult(True, 1, 1, abort_reason='test'); print(r.abort_reason)"`

### Task 2: UPDATE `clickbot/process_executor.py` — Add search_region support to click actions

- **Action**: UPDATE
- **Implement**:
  1. In `_action_click` (L242-263): read `search_region = target.get("search_region")`, convert to tuple if present, pass as `region=` to `vision.find_element()`
  2. Same for `_action_double_click` (L265-280)
- **Pattern**: `vision.find_element()` already accepts `region` parameter (vision.py:191-267)
- **Depends on**: none
- **Validate**: `python -c "from clickbot.process_executor import ProcessExecutor; print('search_region support added')"`

### Task 3: UPDATE `config/processes/1040.json` — Fix Stage 3 (locked client checkbox + locked_2)

- **Action**: UPDATE
- **Implement**: Replace Stage 3 with a `multi` action containing:
  1. **Sub-action 1** (conditional): Check if `file_extension_option_unchecked.png` visible
     - if_true: click `file_extension_option_unchecked.png` (check it)
     - if_false: "continue" (already checked, locked client case)
     - wait_after: 0.5
  2. **Sub-action 2**: click `continue_blue.png`, wait_after: 1.5
  3. **Sub-action 3** (conditional): Check if `locked_2.png` visible
     - if_true: click `unlock_and_save.png`
     - if_false: "continue" (normal, non-locked case)
     - wait_after: 1.0
  4. Keep `verify_next: "1040/04_federal_extension.png"`
- **Pattern**: Nested conditional inside multi works — see `_action_multi` (process_executor.py:733) calling `_execute_step` which routes to `_action_conditional`
- **Depends on**: none
- **Validate**: `python -c "import json; d=json.load(open('config/processes/1040.json')); s3=[s for s in d['stages'] if s['id']==3][0]; assert s3['action']=='multi'; assert len(s3['actions'])==3; print('Stage 3 OK')"`

### Task 4: UPDATE `config/processes/1040.json` — Fix Stage 12 (wizard search_region)

- **Action**: UPDATE
- **Implement**: In Stage 12 `if_false.actions`, update the `no_default.png` conditional click:
  1. Add `"search_region": [560, 340, 800, 400]` to the target (center area of 1920x1080 screen)
  2. Increase `wait_after` from 2.0 to 3.0 for the "save changes" dialog
  3. Also add `"search_region"` to the `clients_button.png` click in the abort sequence — the Clients menu button is in the top-left, region `[0, 0, 300, 80]`
- **Pattern**: Uses new `search_region` feature from Task 2
- **Depends on**: Task 2
- **Validate**: `python -c "import json; d=json.load(open('config/processes/1040.json')); s12=[s for s in d['stages'] if s['id']==12][0]; actions=s12['if_false']['actions']; print([a.get('target',{}).get('search_region') for a in actions if isinstance(a,dict)])"`

### Task 5: UPDATE `config/processes/1040.json` — Fix Stage 16 (clean abort)

- **Action**: UPDATE
- **Implement**: Replace Stage 16 `if_false` with abort pattern:
  ```json
  "if_false": {
    "abort": true,
    "abort_reason": "FAIL: Alerts not passed",
    "actions": [
      {
        "action": "click",
        "target": { "image": "common/clients_button.png" },
        "wait_after": 2.0
      }
    ]
  }
  ```
- **Pattern**: Identical to Stage 12 abort pattern (1040.json:133-156)
- **Depends on**: Task 1 (abort_reason in ExecutionResult)
- **Validate**: `python -c "import json; d=json.load(open('config/processes/1040.json')); s16=[s for s in d['stages'] if s['id']==16][0]; assert s16['if_false']['abort']==True; print('Stage 16 abort OK')"`

### Task 6: UPDATE `config/processes/1040.json` — Fix Stage 18 (clean abort)

- **Action**: UPDATE
- **Implement**: Replace Stage 18 `if_false` with abort pattern:
  ```json
  "if_false": {
    "abort": true,
    "abort_reason": "FAIL: Submit unsuccessful",
    "actions": [
      {
        "action": "click",
        "target": { "image": "common/clients_button.png" },
        "wait_after": 2.0
      }
    ]
  }
  ```
- **Pattern**: Same as Task 5
- **Depends on**: Task 1
- **Validate**: `python -c "import json; d=json.load(open('config/processes/1040.json')); s18=[s for s in d['stages'] if s['id']==18][0]; assert s18['if_false']['abort']==True; print('Stage 18 abort OK')"`

### Task 7: UPDATE `config/processes/1040.json` — Add abort_reason to Stage 12

- **Action**: UPDATE
- **Implement**: Add `"abort_reason": "FAIL: Wizard (Stage 12)"` to the existing Stage 12 `if_false` abort dict
- **Depends on**: Task 1
- **Validate**: `python -c "import json; d=json.load(open('config/processes/1040.json')); s12=[s for s in d['stages'] if s['id']==12][0]; assert 'abort_reason' in s12['if_false']; print(s12['if_false']['abort_reason'])"`

### Task 8: UPDATE `clickbot/vision.py` — Add client_id to ClientRow

- **Action**: UPDATE
- **Implement**:
  1. Add `client_id: str = ""` field to `ClientRow` dataclass (L618-625), between `client_name` and `return_type`
  2. Update `_scan_visible_clients` (L905-994):
     - Call `get_column_positions(extra_columns=["ssn_ein"])` instead of `get_column_positions()` in `find_next_client` (L1026)
     - After reading `client_name` for a candidate row (L953), also read `ssn_ein` via `_read_single_cell("ssn_ein", row_y, column_positions, settings)`
     - Include `client_id=ssn_ein` in the returned `ClientRow` (L982-988)
- **Pattern**: `_read_single_cell` (vision.py:793-829) already supports any column name. SSN/EIN config exists in settings.json L56.
- **Depends on**: none
- **Validate**: `python -c "from clickbot.vision import ClientRow; r = ClientRow(0, 0, 'Test', '12-345', '1040', ''); print(r.client_id)"`

### Task 9: UPDATE `clickbot/vision.py` — CSV-based client lookup in scan

- **Action**: UPDATE
- **Implement**:
  1. Add parameter `csv_records: Optional[List] = None` to `_scan_visible_clients` (L905-910) and `find_next_client` (L997-1001)
  2. In `_scan_visible_clients`: if `csv_records` is provided, build a lookup set of non-TODO keys: `skip_keys = {(r.client_name, r.client_id, r.return_type) for r in csv_records if r.status != "TODO"}`
  3. Replace the `client_name in processed_clients` check (L963) with: `(client_name, ssn_ein, selected_return_type) in skip_keys` when csv_records is available
  4. Keep `processed_clients` parameter for backward compatibility — use it when `csv_records is None`
  5. In `find_next_client`: pass `csv_records` through to `_scan_visible_clients`
- **Pattern**: Existing processed_clients check at vision.py:963
- **Depends on**: Task 8
- **Validate**: `python -c "from clickbot.vision import find_next_client; import inspect; sig = inspect.signature(find_next_client); print('csv_records' in sig.parameters)"`

### Task 10: UPDATE `clickbot/vision.py` — Auto-status-update during scan

- **Action**: UPDATE
- **Implement**:
  1. Add parameter `status_updates: Optional[List] = None` to `_scan_visible_clients`
  2. In the "non-empty fed_ef_status" branch (L942-949): when `csv_records` is provided:
     - Read `ssn_ein` via `_read_single_cell`
     - Read `return_type` via `_read_single_cell` + `normalize_return_type`
     - Build key `(client_name, ssn_ein, return_type)`
     - Look up in csv_records: if CSV status differs from TaxAct fed_ef_status → append `(client_name, ssn_ein, return_type, fed_ef_status)` to `status_updates` list
  3. Return `status_updates` alongside existing return value (add to the tuple)
  4. In `find_next_client`: collect and return status_updates from all scan iterations
- **Pattern**: Follows existing OCR read pattern with `_read_single_cell` (vision.py:793)
- **Depends on**: Task 9
- **Validate**: Code review — auto-update logic reads 2 extra cells per skipped row

### Task 11: UPDATE `clickbot/bot_controller.py` — Add csv_path + locked_1 handling

- **Action**: UPDATE
- **Implement**:
  1. Add `csv_path: Optional[Path] = None` parameter to `BotController.__init__` (L48)
  2. Store as `self.csv_path = csv_path`
  3. After the double-click (L259, `executor.double_click(..., wait=4.0)`), add locked_1 check:
     ```python
     # Check for locked client dialog
     locked = vision.find_element("common/locked_1.png", retry_count=1)
     if locked is not None:
         self._send_log(f"Client is locked, dismissing dialog...")
         vision.find_and_click("common/ok_default.png", wait_after=2.0)
     ```
  4. This runs for ALL return types (1040, 1120, 1120S) — locked clients can appear for any type
- **Pattern**: Follows existing `vision.find_element` + `vision.find_and_click` pattern used in `_recover_to_client_manager` (bot_controller.py:137-143)
- **Depends on**: none
- **Validate**: `python -c "from clickbot.bot_controller import BotController; import inspect; sig = inspect.signature(BotController.__init__); print('csv_path' in sig.parameters)"`

### Task 12: UPDATE `clickbot/bot_controller.py` — Refactor _run() for CSV tracking

- **Action**: UPDATE
- **Implement**:
  1. In `_run()` (L186-287), replace `ClientTracker` usage:
     ```python
     from clickbot.preprocessor import load_csv, update_client_status

     # Load CSV if path provided
     csv_records = None
     if self.csv_path and self.csv_path.exists():
         csv_records = load_csv(self.csv_path)
         todo_count = sum(1 for r in csv_records if r.return_type == self.selected_return_type and r.status == "TODO")
         self._send_log(f"CSV loaded: {todo_count} TODO clients for {self.selected_return_type}")
     ```
  2. Replace `find_next_client` call (L224-228): pass `csv_records=csv_records` instead of `processed_clients=tracker.processed`
  3. Handle auto-status-updates returned by `find_next_client`:
     ```python
     if status_updates and self.csv_path:
         for name, cid, rtype, new_status in status_updates:
             update_client_status(self.csv_path, name, cid, rtype, new_status)
             self._send_log(f"Auto-updated: {name} -> {new_status}")
         csv_records = load_csv(self.csv_path)  # Reload after updates
     ```
  4. After process execution (L276-284), update CSV:
     ```python
     if self.csv_path:
         if result.success:
             update_client_status(self.csv_path, client_row.client_name,
                                  client_row.client_id, self.selected_return_type, "Submitted")
         elif result.abort_reason:
             update_client_status(self.csv_path, client_row.client_name,
                                  client_row.client_id, self.selected_return_type, result.abort_reason)
         else:
             fail_status = f"FAIL: {result.error_message or 'Unknown error'}"
             update_client_status(self.csv_path, client_row.client_name,
                                  client_row.client_id, self.selected_return_type, fail_status)
         csv_records = load_csv(self.csv_path)  # Reload for next iteration
     ```
  5. Remove `tracker = ClientTracker()` and `tracker.mark_processed()` calls when csv_records is available
  6. Keep backward compatibility: if `csv_path is None`, use `ClientTracker` as before
- **Pattern**: `update_client_status` already exists in preprocessor.py:259-298
- **Depends on**: Tasks 1, 9, 10, 11
- **Validate**: Code review — _run() uses CSV for tracking when csv_path is provided

### Task 13: UPDATE `clickbot/gui.py` — Pass csv_path to BotController

- **Action**: UPDATE
- **Implement**:
  1. In `_start_bot` (L715-735): pass `csv_path=self._csv_path` to `BotController` constructor:
     ```python
     self.controller = BotController(
         self.settings,
         selected_return_type=selected_return_type,
         csv_path=self._csv_path
     )
     ```
  2. After bot finishes (when `BotState.IDLE` detected in `_poll_messages` L764): reload CSV to refresh status counts:
     ```python
     if self._csv_path:
         self._load_csv_file(self._csv_path)
     ```
- **Pattern**: `_load_csv_file` (gui.py:569-599) already refreshes counts display
- **Depends on**: Task 11
- **Validate**: Code review — BotController receives csv_path from GUI

### Task 14: ADD Unit Tests

- **Action**: ADD
- **Implement**: Add tests in `tests/unit/` for new functionality:
  1. `test_process_executor.py`:
     - Test `ExecutionResult.abort_reason` field
     - Test `_action_click` with `search_region` in target
     - Test `_execute_branch` stores `abort_reason` from JSON
  2. `test_vision.py`:
     - Test `ClientRow` with `client_id` field
     - Test `_scan_visible_clients` with `csv_records` parameter (mocked OCR)
  3. `test_bot_controller.py`:
     - Test `BotController.__init__` accepts `csv_path`
     - Test locked_1 handling logic (mocked vision calls)
  4. `test_1040_process.py`:
     - Test 1040.json loads and validates (all stages parse correctly)
     - Test Stage 3 has 3 sub-actions (conditional + click + conditional)
     - Test Stages 12, 16, 18 have `abort: true` and `abort_reason`
- **Pattern**: Existing test patterns in `tests/unit/` (mocked pyautogui, vision)
- **Depends on**: Tasks 1-13
- **Validate**: `pytest tests/unit/ -v`

## Testing Requirements

Tests to be written during /execute:

- [ ] ExecutionResult.abort_reason propagation from JSON abort branch
- [ ] search_region passed through to vision.find_element
- [ ] 1040.json Stage 3: conditional checkbox + locked_2 handling parses correctly
- [ ] 1040.json Stages 12, 16, 18: abort + abort_reason present
- [ ] ClientRow.client_id field works
- [ ] _scan_visible_clients with csv_records skips non-TODO clients
- [ ] BotController accepts csv_path parameter
- [ ] Edge case: csv_path is None -> backward-compatible in-memory tracking
- [ ] Edge case: locked_1 not found -> no action taken (normal client)

**Test Levels**: Unit (mocked dependencies)

## Bug Handling

During implementation:
- Bugs caused by THESE changes -> Fix immediately
- Pre-existing bugs discovered -> Document in `.agents/bugs/`, do NOT fix
- NEVER modify working code outside the scope of this plan

## Rollback Strategy

If implementation fails:
1. `git stash` or `git checkout .` to revert changes
2. CSV files in `C:\TaxActBot\logs\` are not affected (read-only until bot runs)
3. 1120/1120S processes are not modified — only 1040.json changes

## Manual Verification

After implementation, manually verify:
- [ ] Bot starts with CSV loaded, shows TODO count in log
- [ ] Processing 1040 client -> CSV updated to "Submitted"
- [ ] Wizard at Stage 12 -> CSV updated to "FAIL: Wizard (Stage 12)"
- [ ] Locked client: locked_1 dialog dismissed, locked_2 popup handled, processing continues
- [ ] Stage 3 with already-checked File Extension: bot skips checkbox click, only clicks Continue
- [ ] After bot run: GUI refreshes CSV status counts
- [ ] 1120S process still works unchanged (backward compat)
- [ ] Auto-update: client with "Ext. Accepted" in TaxAct but "Submitted" in CSV -> CSV updated

## Notes

- `no_default.png` search_region `[560, 340, 800, 400]` covers the center of a 1920x1080 screen where the "save changes" dialog appears. May need calibration.
- The auto-status-update (Task 10) adds 2 extra OCR calls per skipped row during scanning. If this causes performance issues, it can be disabled by not passing csv_records.
- `state.py` is NOT deleted — it remains for backward compatibility when csv_path is None. It can be removed in a future cleanup.
- The `update_client_status` function in preprocessor.py rewrites the entire CSV on each update. This is fine for ~100-500 clients but could be optimized with in-memory caching for larger datasets.

## Confidence Score: 7/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 9/10 | Clear patterns: abort branches, conditional actions, CSV CRUD all exist |
| **External Knowledge** | 9/10 | Pure Python, no external APIs or new libraries |
| **Risk** | 6/10 | Multiple conditional branches in JSON, OCR timing sensitivity, locked client flow untested |
| **Dependencies** | 5/10 | 6+ files affected, changes cascade through executor -> controller -> GUI |
| **Clarity** | 7/10 | Core requirements clear, but locked client edge cases (timing, dialog matching) may need tuning |
| **Testability** | 7/10 | Unit tests via mocks, but real validation requires TaxAct with locked clients and 1040 returns |

**Overall: 7/10** — Codebase patterns are strong and CSV infrastructure exists, but the number of interconnected changes (6+ files) and the locked client flow (untested against real TaxAct) introduce moderate risk.
