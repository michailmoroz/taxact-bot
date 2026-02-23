# Plan: Phase 7 - Step Validation & Speed Optimization (1120S)

## User Story

Als Steuerberater möchte ich, dass der Bot nach jedem Klick validiert, dass TaxAct den richtigen nächsten Screen anzeigt, damit Fehler sofort erkannt und Klicks wiederholt werden, statt dass der Bot blind weiterklickt.

## Acceptance Criteria

- [ ] Bot validiert nach jedem Step via eindeutigen Screen-Header (Template Matching)
- [ ] Bot wartet dynamisch (3Hz Polling) statt fester Wartezeiten
- [ ] Bot wiederholt einen Klick automatisch wenn Screen nicht gewechselt hat (max 3x)
- [ ] Bot gibt nach max Retries auf und wechselt zu Error-Recovery
- [ ] 1120S-Prozess korrigiert auf 20 konsolidierte Stages
- [ ] Bot läuft stabil über 10+ 1120S-Clients im Loop ohne Fehler

## Context

Der Bot hat feste `wait_after`-Zeiten und validiert nicht, ob TaxAct korrekt reagiert hat. Phase 7 ersetzt dieses blinde Warten durch verifizierte Screen-Erkennung: Jeder Screen hat einen eindeutigen Header-Text (z.B. "Tell Us About Your S Corporation"), der als Template-Bild in `assets/verify/1120S/` vorliegt. Nach jedem Klick pollt der Bot bis der Header des nächsten Screens erscheint.

**Scope:** Nur 1120S. Der 1120-Prozess wird in Phase 9 behandelt.

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `clickbot/vision.py` | `find_element()` mit Retry-Logik | 120-191 |
| `clickbot/vision.py` | `scroll_until_visible()` — bestehendes Poll-Pattern | 221-274 |
| `clickbot/process_executor.py` | `execute()` Step-Loop mit `wait_after` | 70-141 |
| `clickbot/process_executor.py` | `_action_click()` — Klick ohne Validierung | 195-216 |
| `clickbot/process_executor.py` | `_action_conditional()` — Branch-Logik | 294-353 |
| `config/processes/1120S.json` | Aktuell 23 Steps, wird auf 20 Stages reduziert | full |
| `config/settings.json` | Timing/Vision-Konfiguration | full |

### Verification Screenshots (vorhanden in `assets/verify/1120S/`)
| File | Screen-Header |
|------|--------------|
| `01_popup_add_remove.png` | "Add / Remove State(s)" |
| `02_s_corp_view.png` | "U.S. Income Tax Return for an S Corporation" |
| `03_efile_center.png` | "Submit Electronic Filing Return" |
| `04_file_extension.png` | "File Extension" |
| `05_extension_intro.png` | "We'll walk you through filing an extension" |
| `06_s_corp_name.png` | "Tell Us About Your S Corporation" |
| `07_address.png` | "address information" |
| `08_ein.png` | "EIN" |
| `09_calendar_year.png` | "return based on a calendar year" |
| `10_who_signing.png` | "Who is signing the return?" |
| `11_ero_statement.png` | "The ERO must read and acknowledge" |
| `12_email_notification.png` | "Get Notified About Your Extension" |
| `13_extension_payment.png` | "Help Us Calculate Your Extension Payment" |
| `14_review_alerts.png` | "Almost Done! Let's Review for Alerts" |
| `15_good_to_go.png` | "You're Good to Go!" |
| `16_efile_confirm.png` | "Okay, it's finally time to E-File" |
| `17_done.png` | "Done!" |
| `18_state_extension.png` | "Would You Like to File a State Extension?" |
| `19_filing_complete.png` | "Filing Extension - Complete" |
| `20_add_client.png` | "Would you like to add a new TaxAct 2025 client" |

### Patterns to Follow
- `scroll_until_visible()` (vision.py:221-274) — Poll+Timeout Pattern
- `find_element()` (vision.py:120-191) — Template Matching mit Retry

## Dependencies

- **New Packages**: none
- **Affected Modules**: vision.py, process_executor.py, 1120S.json, settings.json
- **Breaking Changes**: Nein — Steps ohne `verify_screen` behalten `wait_after` Verhalten

## Tasks

### Task 1: ADD `retry_count` parameter to `find_element()`

- **Action**: UPDATE `clickbot/vision.py`
- **Implement**: Optionalen `retry_count` Parameter zu `find_element()` hinzufügen (Zeile 120):
  ```python
  def find_element(
      image_path: str,
      confidence: Optional[float] = None,
      fallback_coords: Optional[Tuple[int, int]] = None,
      region: Optional[Tuple[int, int, int, int]] = None,
      retry_count: Optional[int] = None
  ) -> Optional[Tuple[int, int]]:
  ```
  In der Retry-Loop (Zeile 158):
  ```python
  retries = retry_count if retry_count is not None else _config["retry_count"]
  for attempt in range(retries):
  ```
  Damit kann `wait_for_element()` mit `retry_count=1` aufrufen (ein Check pro Poll, kein internes Retry).
- **Depends on**: none
- **Validate**: Bestehende Aufrufe bleiben unverändert (default = config value)

### Task 2: ADD `wait_for_element()` to `clickbot/vision.py`

- **Action**: ADD to `clickbot/vision.py` (nach `find_element()`, ca. Zeile 192)
- **Implement**:
  ```python
  def wait_for_element(
      image_path: str,
      timeout: float = 10.0,
      poll_interval: float = 0.333,
      confidence: Optional[float] = None,
      region: Optional[Tuple[int, int, int, int]] = None
  ) -> Optional[Tuple[int, int]]:
      """Poll screen until element appears or timeout.

      Uses SikuliX-style polling (default 3Hz scan rate).
      Unlike find_element(), does NOT use fallback_coords.

      Returns:
          (x, y) if found, None on timeout
      """
      deadline = time.time() + timeout
      while time.time() < deadline:
          coords = find_element(
              image_path, confidence,
              fallback_coords=None,
              region=region,
              retry_count=1
          )
          if coords is not None:
              return coords
          time.sleep(poll_interval)
      return None
  ```
- **Pattern**: Reference `vision.py:221-274` (scroll_until_visible)
- **Depends on**: Task 1
- **Validate**: `python -c "from clickbot.vision import wait_for_element; print('OK')"`

### Task 3: ADD validation settings to `config/settings.json`

- **Action**: UPDATE `config/settings.json`
- **Implement**: Neuer Abschnitt:
  ```json
  "validation": {
    "enabled": true,
    "poll_interval_ms": 333,
    "step_timeout_s": 10.0,
    "max_retries": 3,
    "min_wait_after_ms": 200,
    "verify_base_path": "verify"
  }
  ```
  - `verify_base_path`: Relativer Pfad unter `assets/` für Verify-Templates
- **Depends on**: none
- **Validate**: `python -c "import json; c=json.load(open('config/settings.json')); print(c['validation'])"`

### Task 4: REWRITE `config/processes/1120S.json` — 20 konsolidierte Stages

- **Action**: REWRITE `config/processes/1120S.json`
- **Implement**: Komplette Neufassung mit 20 Stages. Jeder Stage hat:
  - `verify_screen`: Template des eindeutigen Screen-Headers (Verifikation DIESES Screens)
  - `verify_next`: Template des nächsten Screen-Headers (Verifikation nach Klick)
  - Konsolidierte Actions (Scroll+Continue als eine Stage, etc.)
  - Entfernung von Step 21 (`click_continue_filing_complete`)

  **Stage-Definitionen:**
  ```json
  {
    "name": "Form 1120S E-File Extension",
    "return_type": "1120S",
    "version": "2.0",
    "description": "20-stage process with screen verification",
    "static_inputs": {},
    "stages": [
      {
        "id": 1,
        "name": "close_popup_if_present",
        "description": "Close Add/Remove State popup if present",
        "verify_screen": "1120S/01_popup_add_remove.png",
        "action": "conditional",
        "condition": { "type": "element_visible", "image": "common/popup_add_remove_states.png" },
        "if_true": { "action": "click", "target": { "image": "common/popup_close_x.png" } },
        "if_false": "continue",
        "verify_next": "1120S/02_s_corp_view.png"
      },
      {
        "id": 2,
        "name": "click_efile_menu",
        "description": "Click E-File in menu bar",
        "verify_screen": "1120S/02_s_corp_view.png",
        "action": "click",
        "target": { "image": "common/efile_menu.png" },
        "verify_next": "1120S/03_efile_center.png"
      },
      ...
    ]
  }
  ```

  **Vollständiges Stage-Mapping:**

  | ID | Name | verify_screen | Action | verify_next |
  |----|------|--------------|--------|-------------|
  | 1 | close_popup_if_present | 01_popup_add_remove | conditional: close X | 02_s_corp_view |
  | 2 | click_efile_menu | 02_s_corp_view | click: efile_menu | 03_efile_center |
  | 3 | click_submit_electronic_filing | 03_efile_center | click: submit_electronic_filing | 04_file_extension |
  | 4 | select_file_extension_and_continue | 04_file_extension | click: file_extension_option + click: continue_blue | 05_extension_intro |
  | 5 | click_continue_extension_intro | 05_extension_intro | click: continue_green | 06_s_corp_name |
  | 6 | click_continue_s_corp_name | 06_s_corp_name | click: continue_blue | 07_address |
  | 7 | click_continue_address | 07_address | click: continue_blue | 08_ein |
  | 8 | click_continue_ein | 08_ein | click: continue_blue | 09_calendar_year |
  | 9 | click_continue_calendar_year | 09_calendar_year | click: continue_blue | 10_who_signing |
  | 10 | click_continue_who_signing | 10_who_signing | click: continue_blue | 11_ero_statement |
  | 11 | click_continue_ero_statement | 11_ero_statement | click: continue_blue | 12_email_notification |
  | 12 | click_continue_email_notification | 12_email_notification | click: continue_blue | 13_extension_payment |
  | 13 | scroll_and_continue_payment | 13_extension_payment | scroll_until_visible + click: continue_blue | 14_review_alerts |
  | 14 | click_start_alerts | 14_review_alerts | click: start_alerts | 15_good_to_go |
  | 15 | click_continue_good_to_go | 15_good_to_go | click: continue_blue | 16_efile_confirm |
  | 16 | click_submit_efile | 16_efile_confirm | click: submit_efile | 17_done |
  | 17 | click_continue_done | 17_done | click: continue_blue | 18_state_extension |
  | 18 | click_continue_state_extension | 18_state_extension | click: continue_blue | 19_filing_complete |
  | 19 | click_new_return | 19_filing_complete | click: new_return | 20_add_client |
  | 20 | close_add_client_popup | 20_add_client | click: popup_cancel | *(base/end)* |

  **Konsolidierungen:**
  - Alt Steps 4+5 → Neu Stage 4 (select checkbox + continue in einer Stage)
  - Alt Steps 14+15 → Neu Stage 13 (scroll + continue in einer Stage)
  - Alt Step 21 (click_continue_filing_complete) entfernt

  **Conditional Stages (1, 14, 15-16):**
  - Stage 1: `verify_screen` ist optional (Popup erscheint nicht immer)
  - Stage 14: `verify_next` unterscheidet sich je nach Alerts-Ergebnis
    - Good to Go → `15_good_to_go.png`
    - Error → Recovery zum Client Manager (kein verify_next nötig)

- **Depends on**: Task 3
- **Validate**: `python -c "import json; p=json.load(open('config/processes/1120S.json')); print(f\"{len(p['stages'])} stages\")"`

### Task 5: REFACTOR `process_executor.execute()` for verification

- **Action**: UPDATE `clickbot/process_executor.py`
- **Implement**: Die Step-Loop refactoren für `verify_next`-Unterstützung:

  **In `execute()`** — nach Step-Ausführung (ca. Zeile 130):
  ```python
  # After step execution: verify next screen
  verify_next = step.get("verify_next")
  validation_cfg = self.settings.get("validation", {})
  validation_enabled = validation_cfg.get("enabled", False)

  if verify_next and validation_enabled:
      verify_path = self._resolve_verify_path(verify_next)
      success = self._wait_and_verify(step, verify_path, validation_cfg)
      if not success:
          error_msg = f"Screen verification failed after: {step_name}"
          self._send_error(error_msg)
          sounds.play_error()
          return ExecutionResult(
              success=False, steps_completed=i,
              total_steps=total_steps, error_message=error_msg,
              error_step=step["id"]
          )
  else:
      # Fallback: fixed wait_after (backward compatible)
      wait_after = step.get("wait_after", self.settings.get("timing", {}).get("default_wait", 2.0))
      if wait_after > 0:
          time.sleep(wait_after)
  ```

  Auch `verify_screen` als optionale Pre-Check Unterstützung:
  ```python
  # Before step execution: optionally verify we're on the right screen
  verify_screen = step.get("verify_screen")
  if verify_screen and validation_enabled:
      verify_path = self._resolve_verify_path(verify_screen)
      on_screen = vision.find_element(verify_path, retry_count=1, fallback_coords=None)
      if on_screen is None:
          logger.warning(f"  -> Pre-check: expected screen not detected: {verify_screen}")
  ```

  **Key-Feld Unterschied:**
  - `verify_screen`: "Auf welchem Screen BIN ich?" (Pre-Check, Warnung bei Mismatch)
  - `verify_next`: "Welcher Screen SOLL als nächstes kommen?" (Post-Click Polling + Retry)

- **Pattern**: Reference `process_executor.py:98-141`
- **Depends on**: Task 2, Task 3
- **Validate**: Bot startet ohne Fehler, Steps ohne `verify_next` verwenden `wait_after`

### Task 6: ADD `_wait_and_verify()` and `_resolve_verify_path()` to `ProcessExecutor`

- **Action**: ADD to `clickbot/process_executor.py`
- **Implement**:
  ```python
  def _resolve_verify_path(self, verify_image: str) -> str:
      """Resolve verify image path relative to verify_base_path."""
      base = self.settings.get("validation", {}).get("verify_base_path", "verify")
      return f"{base}/{verify_image}"

  def _wait_and_verify(
      self,
      step: Dict[str, Any],
      verify_path: str,
      validation_cfg: Dict[str, Any]
  ) -> bool:
      """Wait for next screen and retry click if needed.

      1. Poll for expected screen header (timeout from config)
      2. If found → success
      3. If timeout → re-locate and retry click (max_retries)
      4. If max retries exhausted → return False
      """
      timeout = validation_cfg.get("step_timeout_s", 10.0)
      poll_interval = validation_cfg.get("poll_interval_ms", 333) / 1000
      max_retries = validation_cfg.get("max_retries", 3)
      min_wait = validation_cfg.get("min_wait_after_ms", 200) / 1000

      for retry in range(max_retries):
          logger.info(
              f"  -> Verifying: {verify_path} "
              f"(timeout={timeout}s, attempt {retry+1}/{max_retries})"
          )
          coords = vision.wait_for_element(
              verify_path, timeout=timeout, poll_interval=poll_interval
          )

          if coords is not None:
              logger.info(f"  -> Screen verified: {verify_path}")
              time.sleep(min_wait)
              return True

          # Timeout: retry the click
          if retry < max_retries - 1:
              logger.warning(f"  -> Screen not verified, retrying click...")
              self._send_log(f"Retry {retry+1}: {step.get('name', 'unknown')}")
              self._retry_step_click(step)

      logger.error(f"  -> Verification FAILED after {max_retries} attempts")
      return False

  def _retry_step_click(self, step: Dict[str, Any]) -> None:
      """Re-execute the click action of a step for retry."""
      action = step.get("action")
      target = step.get("target", {})

      if action == "click":
          self._action_click(target)
      elif action == "double_click":
          self._action_double_click(target)
      # For conditional/scroll: don't retry click, just wait longer
  ```
- **Depends on**: Task 2, Task 5
- **Validate**: Covered by E2E test

### Task 7: SUPPORT `verify_next` in conditional branches

- **Action**: UPDATE `clickbot/process_executor.py`
- **Implement**: In `_execute_branch()` (ca. Zeile 355): Nach Branch-Ausführung, prüfe ob der Branch ein `verify_next` hat und validiere:
  ```python
  def _execute_branch(self, branch, static_inputs, detected_position=None) -> bool:
      if branch is None or branch == "continue":
          return True

      if isinstance(branch, dict):
          # Execute the branch action (existing code)
          result = ...  # existing logic

          # NEW: verify_next in branch
          verify_next = branch.get("verify_next")
          validation_cfg = self.settings.get("validation", {})
          if verify_next and validation_cfg.get("enabled", False):
              verify_path = self._resolve_verify_path(verify_next)
              if not self._wait_and_verify(branch, verify_path, validation_cfg):
                  return False

          return result
  ```
  Damit kann im 1120S.json z.B. Stage 14 (Alerts) verschiedene `verify_next` je nach Branch haben.
- **Depends on**: Task 6
- **Validate**: Conditional steps mit `verify_next` in Branches funktionieren

### Task 8: HANDLE multi-action stages in process executor

- **Action**: UPDATE `clickbot/process_executor.py`
- **Implement**: Neue Action `multi` für konsolidierte Stages (z.B. Stage 4: checkbox + continue, Stage 13: scroll + continue):
  ```python
  elif action == "multi":
      return self._action_multi(step, static_inputs)

  def _action_multi(self, step: Dict[str, Any], static_inputs: Dict[str, str]) -> bool:
      """Execute multiple sub-actions in sequence."""
      sub_actions = step.get("actions", [])
      for sub in sub_actions:
          if not self._execute_step(sub, static_inputs):
              return False
          sub_wait = sub.get("wait_after", 0.5)
          if sub_wait > 0:
              time.sleep(sub_wait)
      return True
  ```
  Stage 4 in JSON:
  ```json
  {
    "id": 4,
    "name": "select_file_extension_and_continue",
    "action": "multi",
    "actions": [
      { "action": "click", "target": { "image": "common/file_extension_option_unchecked.png" }, "wait_after": 0.5 },
      { "action": "click", "target": { "image": "common/continue_blue.png" } }
    ],
    "verify_next": "1120S/05_extension_intro.png"
  }
  ```
- **Depends on**: none
- **Validate**: `python -c "from clickbot.process_executor import ProcessExecutor; print('OK')"`

## Testing Requirements

- [ ] Unit test: `vision.wait_for_element()` — finds element after N polls
- [ ] Unit test: `vision.wait_for_element()` — timeout returns None
- [ ] Unit test: `ProcessExecutor._wait_and_verify()` — success on first attempt
- [ ] Unit test: `ProcessExecutor._wait_and_verify()` — retry after timeout, success on 2nd
- [ ] Unit test: `ProcessExecutor._wait_and_verify()` — max retries returns False
- [ ] Unit test: Steps without `verify_next` use `wait_after` (backward compatible)
- [ ] Unit test: `_action_multi()` executes sub-actions in sequence
- [ ] E2E test: 1120S full process with verification against real TaxAct

**Test Levels**: Unit for vision.py and process_executor.py, E2E for full process

## Bug Handling

- Bugs caused by THESE changes → Fix immediately
- Pre-existing bugs → Document in `.agents/bugs/`, do NOT fix
- NEVER modify working code outside scope

## Rollback Strategy

1. Set `validation.enabled: false` in settings.json → Falls back to `wait_after`
2. `git stash` or `git checkout .` to revert all changes
3. Process JSONs with `verify_screen`/`verify_next` work without validation (fields ignored)

## Manual Verification

- [ ] Bot startet und führt 1120S mit Screen-Verifikation aus
- [ ] Terminal zeigt "Verifying: verify/1120S/06_s_corp_name.png" → "Screen verified"
- [ ] Bot wartet kürzer als vorher bei schnellem TaxAct
- [ ] Bei langsamem TaxAct: Bot wartet automatisch (bis 10s Timeout)
- [ ] Bei verpasstem Klick: Terminal zeigt "Screen not verified, retrying click..."
- [ ] Nach 3 fehlgeschlagenen Retries: Error + Recovery zum Client Manager
- [ ] `validation.enabled: false` → Bot verhält sich wie bisher
- [ ] 10+ 1120S-Clients im Loop ohne Fehler
- [ ] 1120-Clients laufen weiterhin mit altem `wait_after` (nicht kaputt)

## Notes

- **Nur 1120S**: Dieser Plan berührt NICHT `1120.json`. Der 1120-Prozess läuft weiterhin mit `wait_after`.
- **verify_screen vs verify_next**: `verify_screen` = Pre-Check (optional, nur Warnung). `verify_next` = Post-Click Polling (kritisch, mit Retry).
- **Stage 1 (Popup)**: `verify_screen` ist optional — Popup erscheint nicht immer. `verify_next` wartet auf `02_s_corp_view.png`.
- **Stage 14 (Alerts)**: Error-Fall führt zu Recovery, `verify_next` nur im Success-Branch.
- **Stage 20 (Add Client)**: Letzter Stage, kein `verify_next` nötig (Ende der Iteration).
- **Performance**: Bei 20 Stages mit ~0.5s avg Polling → ~10s statt ~20s feste Waits.
