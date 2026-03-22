# Plan: Phase 10b-1 — 1040 Process Fixes (Abort Handling, Wizard, Locked Clients)

> **Parent Plan**: `phase-10b-csv-integration-and-1040-fixes.md`
> **Sibling**: `phase-10b-2-csv-bot-integration.md`
> **Supersedes**: `phase-10b-csv-bot-integration.md` (OBSOLET)

## User Story

Als Steuerberater moechte ich, dass der 1040-Prozess sauber abbricht wenn Alerts nicht bestehen oder der Wizard erscheint, dass gesperrte Clients korrekt gehandhabt werden, und dass der Bot den genauen Abbruchgrund zurueckmeldet.

## Acceptance Criteria

- [ ] Stage 12: Wizard wird erkannt, `no_default.png` wird im Zentrum des Screens gefunden und geklickt
- [ ] Stage 16: Sauberer Abort mit `"abort": true` wenn Alerts nicht bestehen
- [ ] Stage 18: Sauberer Abort mit `"abort": true` wenn Submit nicht erfolgreich
- [ ] Alle Abort-Stages liefern spezifischen `abort_reason` String
- [ ] `ExecutionResult` enthaelt `abort_reason` Feld
- [ ] Locked Client: `locked_1.png` nach Doppelklick erkannt, `ok_default.png` geklickt
- [ ] Locked Client Stage 3: Checkbox nur geklickt wenn unchecked, `locked_2.png` wird bis zu 5s abgewartet
- [ ] 1120/1120S Prozesse weiterhin unveraendert funktionsfaehig

## Context

Der 1040-Prozess hat mehrere Schwachstellen: Stage 16/18 brechen nicht sauber ab (kein `abort: true`), Stage 12 findet `no_default.png` nicht zuverlaessig (zu kleines Template, Fullscreen-Suche), und gesperrte Clients werden nicht gehandhabt. Dieser Plan fixt alle 1040-spezifischen Probleme und fuehrt `abort_reason` ein, das spaeter von der CSV-Integration (Plan 10b-2) genutzt wird.

## Research Summary

### Relevant Files

| File | Purpose | Key Lines |
|------|---------|-----------|
| `clickbot/process_executor.py` | ExecutionResult, _action_click, _execute_branch | L27-34, L242-263, L341-411, L413-441 |
| `clickbot/bot_controller.py` | Double-click + locked_1 handling point | L244-259 |
| `config/processes/1040.json` | Stages 3, 12, 16, 18 | Full file (296 lines) |

### Patterns to Follow

- **Abort branch**: `1040.json:133-156` (Stage 12 if_false) — already uses `"abort": true` pattern
- **Conditional in multi**: `process_executor.py:733-753` — `_action_multi` calls `_execute_step` which routes to `_action_conditional`, so nesting works
- **find_element with region**: `vision.py:191-267` — already accepts `region` parameter
- **wait_for_element**: `vision.py:270-318` — polling with timeout, used by verify_next

## Dependencies

- **New Packages**: none
- **Affected Modules**: `process_executor.py`, `bot_controller.py`, `1040.json`
- **Breaking Changes**: No — new fields have defaults, new JSON fields are optional

## Tasks

### Task 1: UPDATE `clickbot/process_executor.py` — Add abort_reason to ExecutionResult

- **Action**: UPDATE
- **Implement**:
  1. Add `abort_reason: Optional[str] = None` to `ExecutionResult` dataclass (L27-34)
  2. Add `self._last_abort_reason: Optional[str] = None` to `ProcessExecutor.__init__` (L47-69)
  3. Reset `self._last_abort_reason = None` at the START of `execute()` (after L96)
  4. In `_execute_branch` (L432-441): when `branch.get("abort")` is True, store `self._last_abort_reason = branch.get("abort_reason")`
  5. In `execute()` error path (L143-153): add `abort_reason=self._last_abort_reason` to the returned ExecutionResult
  6. Also in the verify-failed error path (L163-172): add `abort_reason=self._last_abort_reason`
- **Pattern**: Follows existing `error_message`/`error_step` pattern in ExecutionResult (L33-34)
- **Depends on**: none
- **Validate**: `python -c "from clickbot.process_executor import ExecutionResult; r = ExecutionResult(True, 1, 1, abort_reason='FAIL: test'); assert r.abort_reason == 'FAIL: test'; print('OK')"`

### Task 2: UPDATE `clickbot/process_executor.py` — Add search_region to click actions

- **Action**: UPDATE
- **Implement**:
  1. In `_action_click` (L242-263): read `search_region = target.get("search_region")`, convert to tuple if list, pass as `region=search_region` to `vision.find_element()` call (L253)
  2. Same pattern in `_action_double_click` (L265-280): read and pass `search_region`
- **Pattern**: `vision.find_element()` already accepts `region` parameter (L196)
- **Depends on**: none
- **Validate**: `python -c "from clickbot.process_executor import ProcessExecutor; print('search_region support OK')"`

### Task 3: UPDATE `clickbot/process_executor.py` — Add timeout to element_visible condition

- **Action**: UPDATE
- **Implement**:
  In `_action_conditional` (L346-358), when `condition_type == "element_visible"`:
  1. Read `timeout = condition.get("timeout")`
  2. If timeout is set: use `vision.wait_for_element(image, timeout=timeout, confidence=confidence, base_path=cond_base_path, stop_event=self.stop_event)` instead of `vision.find_element()`
  3. If timeout is not set: keep current `vision.find_element()` behavior (unchanged)

  ```python
  if condition_type == "element_visible":
      image = condition.get("image")
      confidence = condition.get("confidence")
      timeout = condition.get("timeout")
      # ... existing base_path logic ...
      if timeout:
          is_visible = vision.wait_for_element(
              image, timeout=timeout, confidence=confidence,
              base_path=cond_base_path, stop_event=self.stop_event
          ) is not None
      else:
          is_visible = vision.find_element(
              image, confidence, fallback_coords=None, base_path=cond_base_path
          ) is not None
  ```
- **Pattern**: `wait_for_element` already used in `_wait_and_verify` (process_executor.py:646-649)
- **Depends on**: none
- **Validate**: `python -c "from clickbot.process_executor import ProcessExecutor; print('timeout condition OK')"`

### Task 4: UPDATE `config/processes/1040.json` — Fix Stage 3 (locked checkbox + locked_2)

- **Action**: UPDATE
- **Implement**: Replace current Stage 3 (L26-45) with:
  ```json
  {
    "id": 3,
    "name": "select_file_extension_and_continue",
    "description": "Check File Extension (if unchecked), click Continue, handle locked_2 popup if present",
    "verify_screen": "1040/03_file_extension.png",
    "action": "multi",
    "actions": [
      {
        "action": "conditional",
        "condition": {
          "type": "element_visible",
          "image": "common/file_extension_option_unchecked.png"
        },
        "if_true": {
          "action": "click",
          "target": { "image": "common/file_extension_option_unchecked.png" }
        },
        "if_false": "continue",
        "wait_after": 0.5
      },
      {
        "action": "click",
        "target": { "image": "common/continue_blue.png" },
        "wait_after": 2.0
      },
      {
        "action": "conditional",
        "condition": {
          "type": "element_visible",
          "image": "common/locked_2.png",
          "timeout": 5.0
        },
        "if_true": {
          "action": "click",
          "target": { "image": "common/unlock_and_save.png" }
        },
        "if_false": "continue",
        "wait_after": 1.0
      }
    ],
    "verify_next": "1040/04_federal_extension.png"
  }
  ```
  Sub-action 1: Only check the checkbox if unchecked (locked clients have it pre-checked).
  Sub-action 2: Click Continue, wait 2s for TaxAct to respond.
  Sub-action 3: Wait up to 5s for `locked_2.png`. If it appears, click `unlock_and_save.png`. If not (normal case), continue.
  verify_next: Confirms we reached `04_federal_extension.png` in both cases.
- **Pattern**: Nested conditional inside multi — validated by `_action_multi` calling `_execute_step` (process_executor.py:733-753)
- **Depends on**: Task 3 (timeout in element_visible condition)
- **Validate**: `python -c "import json; d=json.load(open('config/processes/1040.json')); s3=[s for s in d['stages'] if s['id']==3][0]; assert s3['action']=='multi'; assert len(s3['actions'])==3; print('Stage 3:', [a.get('action') for a in s3['actions']])"`

### Task 5: UPDATE `config/processes/1040.json` — Fix Stage 12 (wizard + search_region + abort_reason)

- **Action**: UPDATE
- **Implement**: Update Stage 12 `if_false` (L133-156):
  1. Add `"abort_reason": "FAIL: Wizard (Stage 12)"` to the abort dict
  2. In the `clients_button.png` click action: add `"search_region": [0, 0, 300, 80]` (top-left menu area)
  3. In the `no_default.png` conditional: add `"search_region": [560, 340, 800, 400]` to the target (center of 1920x1080)
  4. Increase `wait_after` on the `no_default.png` conditional from 2.0 to 3.0

  Updated if_false:
  ```json
  "if_false": {
    "abort": true,
    "abort_reason": "FAIL: Wizard (Stage 12)",
    "description": "Bail out: click Clients, dismiss save-changes dialog, then stop process",
    "actions": [
      {
        "action": "click",
        "target": { "image": "common/clients_button.png", "search_region": [0, 0, 300, 80] },
        "wait_after": 1.5
      },
      {
        "action": "conditional",
        "condition": {
          "type": "element_visible",
          "image": "1040/no_default.png"
        },
        "if_true": {
          "action": "click",
          "target": { "image": "1040/no_default.png", "search_region": [560, 340, 800, 400] }
        },
        "if_false": "continue",
        "wait_after": 3.0
      }
    ]
  }
  ```
- **Pattern**: Existing abort pattern at `1040.json:133-156`
- **Depends on**: Tasks 1, 2
- **Validate**: `python -c "import json; d=json.load(open('config/processes/1040.json')); s12=[s for s in d['stages'] if s['id']==12][0]; f=s12['if_false']; assert f['abort_reason']=='FAIL: Wizard (Stage 12)'; print('Stage 12 OK')"`

### Task 6: UPDATE `config/processes/1040.json` — Fix Stage 16 (clean abort)

- **Action**: UPDATE
- **Implement**: Replace Stage 16 `if_false` (L249-253) with abort pattern:
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
- **Pattern**: Identical to Stage 12 abort pattern
- **Depends on**: Task 1
- **Validate**: `python -c "import json; d=json.load(open('config/processes/1040.json')); s16=[s for s in d['stages'] if s['id']==16][0]; assert s16['if_false']['abort']==True; assert s16['if_false']['abort_reason']=='FAIL: Alerts not passed'; print('Stage 16 OK')"`

### Task 7: UPDATE `config/processes/1040.json` — Fix Stage 18 (clean abort)

- **Action**: UPDATE
- **Implement**: Replace Stage 18 `if_false` (L280-284) with abort pattern:
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
- **Pattern**: Identical to Stage 12/16 abort pattern
- **Depends on**: Task 1
- **Validate**: `python -c "import json; d=json.load(open('config/processes/1040.json')); s18=[s for s in d['stages'] if s['id']==18][0]; assert s18['if_false']['abort']==True; assert s18['if_false']['abort_reason']=='FAIL: Submit unsuccessful'; print('Stage 18 OK')"`

### Task 8: UPDATE `clickbot/bot_controller.py` — Add locked_1 handling after double-click

- **Action**: UPDATE
- **Implement**: After the double-click call (L259, `executor.double_click(..., wait=4.0)`), add:
  ```python
  # Check for locked client dialog (text "Practice Administrator." in center)
  locked = vision.find_element(
      "common/locked_1.png", retry_count=1,
      region=(800, 580, 300, 40)
  )
  if locked is not None:
      self._send_log(f"Client is locked, dismissing dialog...")
      vision.find_and_click("common/ok_default.png", wait_after=2.0)
  ```
  This runs for ALL return types (1040, 1120, 1120S) since any client can be locked.
- **Pattern**: Follows existing `vision.find_element` + `vision.find_and_click` used in `_recover_to_client_manager` (bot_controller.py:137-143)
- **Depends on**: none
- **Validate**: Code review — locked_1 check is between double_click and process execution

### Task 9: ADD Unit Tests for 1040 Fixes

- **Action**: ADD
- **Implement**: Create/update tests in `tests/unit/`:
  1. **test_process_executor.py**:
     - Test `ExecutionResult.abort_reason` field exists and defaults to None
     - Test `_execute_branch` with `{"abort": true, "abort_reason": "FAIL: test"}` sets `_last_abort_reason`
     - Test `_action_click` passes `search_region` from target to `vision.find_element` (mock vision)
     - Test `_action_conditional` with `timeout` in condition uses `wait_for_element` instead of `find_element`
  2. **test_1040_process.py** (new file):
     - Test `1040.json` loads without errors
     - Test Stage 3 has 3 sub-actions (conditional, click, conditional)
     - Test Stage 3 sub-action 3 has `timeout: 5.0` in condition
     - Test Stage 12 has `abort_reason: "FAIL: Wizard (Stage 12)"`
     - Test Stage 16 has `abort: true` and `abort_reason: "FAIL: Alerts not passed"`
     - Test Stage 18 has `abort: true` and `abort_reason: "FAIL: Submit unsuccessful"`
- **Pattern**: Existing test patterns in `tests/unit/` with mocked pyautogui/vision
- **Depends on**: Tasks 1-8
- **Validate**: `pytest tests/unit/ -v`

## Testing Requirements

- [ ] ExecutionResult.abort_reason propagation from JSON abort branch to return value
- [ ] search_region correctly passed through _action_click to vision.find_element
- [ ] timeout in element_visible condition triggers wait_for_element instead of find_element
- [ ] 1040.json Stages 3, 12, 16, 18 parse correctly with new structure
- [ ] Stage 3: conditional checkbox (unchecked=click, checked=skip) works
- [ ] Stage 3: locked_2 wait with 5s timeout, if_true clicks unlock_and_save
- [ ] Edge case: non-locked client → Stage 3 sub-action 3 if_false fires (continue), no delay
- [ ] Edge case: locked_1 not found after double-click → no action (normal client)
- [ ] 1120S process still loads and validates unchanged

**Test Levels**: Unit (mocked dependencies)

## Bug Handling

- Bugs caused by THESE changes → Fix immediately
- Pre-existing bugs → Document in `.agents/bugs/`, do NOT fix
- NEVER modify 1120.json or 1120S.json

## Rollback Strategy

1. `git stash` or `git checkout .` to revert changes
2. Only 3 files modified: `process_executor.py`, `bot_controller.py`, `1040.json`
3. 1120/1120S processes are NOT touched

## Manual Verification

- [ ] Normal 1040 client: processes through all 19 stages successfully
- [ ] Wizard at Stage 12: `no_default.png` found and clicked, process aborts with reason
- [ ] Alerts not passed at Stage 16: `clients_button.png` clicked, process aborts cleanly
- [ ] Locked client: locked_1 dialog dismissed after double-click, processing continues
- [ ] Locked client Stage 3: checkbox already checked → skipped, locked_2 → unlock_and_save clicked
- [ ] Non-locked client Stage 3: checkbox unchecked → clicked, no locked_2 wait
- [ ] 1120S process: unchanged behavior (regression test)

## Notes

- `search_region` coordinates are estimates: `no_default.png` at `[560, 340, 800, 400]` (center), `locked_1.png` at `(800, 580, 300, 40)`. May need calibration with real TaxAct.
- The `timeout: 5.0` on locked_2 condition means the bot waits up to 5s for the popup. For non-locked clients this adds 5s delay at Stage 3. If this is too slow, reduce to 2-3s. **UPDATE**: Actually, `wait_for_element` returns immediately when the element is NOT found after polling. For non-locked clients, `locked_2.png` won't appear and the function returns after the timeout. To avoid the 5s delay for normal clients, we can use a shorter timeout (e.g. 2.0s) since the popup should appear quickly if it appears at all.
- `abort_reason` is stored on the `ProcessExecutor` instance (`_last_abort_reason`). For non-abort failures (element not found, timeout), it remains None. Plan 10b-2 uses this to write specific FAIL reasons to CSV.
- This plan is independent of Plan 10b-2 (CSV Integration). It can be tested and verified without CSV.

## Confidence Score: 8/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 9/10 | Abort branches, conditional actions, find_element with region all exist |
| **External Knowledge** | 10/10 | Pure Python, no external APIs |
| **Risk** | 7/10 | Locked client timing and search_region coordinates may need calibration |
| **Dependencies** | 9/10 | Only 3 files, clear dependency chain |
| **Clarity** | 8/10 | Core flow clear, timing for locked_2 may need tuning |
| **Testability** | 8/10 | Unit tests via mocks, E2E needs real TaxAct with locked + 1040 clients |

**Overall: 8/10** — Small scope (3 files), clear patterns, but locked client timing and search_region coordinates need real-world calibration.
