# Plan: Phase 6 - Loop Mode & State Tracking

## User Story

Als Steuerberater möchte ich, dass der Bot automatisch mehrere Clients nacheinander bearbeitet und dabei keine Clients doppelt verarbeitet, damit ich den Bot starten und alle Clients ohne manuelles Eingreifen bearbeiten lassen kann.

## Acceptance Criteria

- [ ] Bot bearbeitet mehrere Clients in einer Schleife
- [ ] Kein Client wird doppelt bearbeitet (State Tracking)
- [ ] Bot scrollt in Client-Liste wenn alle sichtbaren Clients bearbeitet sind
- [ ] Bei Fehler: Client überspringen, weiter mit nächstem
- [ ] Windows System-Sound bei jeder neuen Iteration
- [ ] Bot stoppt automatisch wenn keine unbearbeiteten Clients mehr
- [ ] GUI zeigt Progress: "Client X von Y"

## Context

Der Bot kann aktuell nur einen Client bearbeiten und stoppt dann. Phase 6 fügt Loop-Mode hinzu: Nach Abschluss einer Iteration kehrt der Bot zum Client Manager zurück, sucht den nächsten unbearbeiteten Client, und wiederholt den Prozess. State Tracking verhindert Endlosschleifen bei fehlgeschlagenen Clients.

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `clickbot/bot_controller.py` | Main loop location - needs loop logic | 123-191 |
| `clickbot/vision.py` | `find_next_client()` - needs scroll support | 619-691 |
| `clickbot/sounds.py` | Sound functions - add iteration sound | 48-123 |
| `clickbot/gui.py` | GUI updates - progress display | 320-337 |
| `config/settings.json` | Config - add loop settings | full |

### Patterns to Follow
- State management via module-level variables (see `sounds.py:25-36`)
- Dataclass for structured data (see `vision.py:490-497` for `ClientRow`)
- Message queue pattern for GUI updates (see `bot_controller.py:108-121`)
- Settings-driven configuration (see `vision.py:37-54`)

## Dependencies

- **New Packages**: none
- **Affected Modules**: bot_controller.py, vision.py, sounds.py, gui.py, settings.json
- **Breaking Changes**: No - existing single-iteration mode will work as before (loop with 1 iteration)

## Tasks

### Task 1: CREATE `clickbot/state.py`

- **Action**: CREATE
- **Implement**: Create ClientTracker class for tracking processed clients
  ```python
  from dataclasses import dataclass, field
  from typing import Set

  @dataclass
  class ClientTracker:
      processed: Set[str] = field(default_factory=set)

      def mark_processed(self, client_name: str) -> None
      def is_processed(self, client_name: str) -> bool
      def get_count(self) -> int
      def clear(self) -> None
  ```
- **Pattern**: Reference `vision.py:490-497` for dataclass pattern
- **Depends on**: none
- **Validate**: `python -c "from clickbot.state import ClientTracker; t = ClientTracker(); t.mark_processed('TEST'); print(t.is_processed('TEST'))"`

### Task 2: ADD `play_iteration()` to `clickbot/sounds.py`

- **Action**: ADD
- **Implement**: Add Windows system sound for new iteration
  ```python
  def play_iteration() -> None:
      """Play Windows system sound for new iteration."""
      if not is_enabled():
          return
      try:
          winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
      except Exception as e:
          logger.warning(f"Could not play iteration sound: {e}")
  ```
- **Pattern**: Reference `sounds.py:48-67` for function structure
- **Depends on**: none
- **Validate**: `python -c "from clickbot import sounds; sounds.set_enabled(True); sounds.play_iteration()"`

### Task 3: ADD scroll support to `vision.find_next_client()`

- **Action**: UPDATE
- **Implement**: Modify `find_next_client()` to accept `processed_clients: Set[str]` parameter and scroll in client list when no unprocessed clients visible
  - Add parameter `processed_clients: Optional[Set[str]] = None`
  - Skip clients that are in `processed_clients` set
  - After scanning visible rows without finding candidate:
    1. Remember last visible client name
    2. Scroll down in client list (scroll_amount from settings)
    3. Re-scan - if last client same as before, we're at end of list
    4. Max 20 scroll attempts to prevent infinite loop
  - Use `executor.scroll()` for scrolling at position (center of table)
- **Pattern**: Reference `vision.py:221-274` for scroll pattern
- **Depends on**: none
- **Validate**: Manual test with TaxAct open

### Task 4: ADD loop settings to `config/settings.json`

- **Action**: UPDATE
- **Implement**: Add loop configuration section
  ```json
  "loop": {
    "scroll_in_table": {
      "x": 400,
      "y": 500,
      "amount": -300,
      "max_attempts": 20
    }
  }
  ```
- **Pattern**: Reference `settings.json:49-58` for nested config
- **Depends on**: none
- **Validate**: `python -c "import json; c=json.load(open('config/settings.json')); print(c['loop'])"`

### Task 5: REFACTOR `bot_controller._run()` for loop mode

- **Action**: UPDATE
- **Implement**: Replace single-iteration logic with loop
  ```python
  def _run(self) -> None:
      from clickbot.state import ClientTracker

      tracker = ClientTracker()
      clients_processed = 0

      while not self.stop_event.is_set():
          # Play iteration sound (except first)
          if clients_processed > 0:
              sounds.play_iteration()

          # Find next client (pass processed set)
          client_result = vision.find_next_client(
              self.settings,
              processed_clients=tracker.processed
          )

          if client_result is None:
              # No more clients
              self._send_complete(f"All done! Processed {clients_processed} clients")
              sounds.play_complete()
              break

          client_row, click_pos = client_result

          # Mark as processed BEFORE starting (prevents retry on failure)
          tracker.mark_processed(client_row.client_name)
          clients_processed += 1

          # Update progress
          self._send_progress(f"Client {clients_processed}")

          # Process client (existing logic)
          executor.double_click(click_pos[0], click_pos[1], wait=4.0)

          result = process_executor.execute(client_row.return_type)

          if not result.success:
              if result.error_message != "Stopped by user":
                  self._send_log(f"SKIPPED: {client_row.client_name} - {result.error_message}")
                  sounds.play_error()
              # Continue to next client (don't break)

      self.state = BotState.IDLE
  ```
- **Pattern**: Reference `bot_controller.py:123-191` for current structure
- **Depends on**: Task 1, Task 2, Task 3, Task 4
- **Validate**: Manual E2E test with TaxAct

### Task 6: ADD `_send_progress()` helper to `bot_controller.py`

- **Action**: ADD
- **Implement**: Add helper method for progress messages
  ```python
  def _send_progress(self, message: str) -> None:
      """Send progress update to GUI."""
      self.message_queue.put(StatusMessage("progress", message))
  ```
- **Pattern**: Reference `process_executor.py:492-502` for message helpers
- **Depends on**: none
- **Validate**: Covered by Task 5 validation

### Task 7: UPDATE GUI to show client count

- **Action**: UPDATE
- **Implement**: Enhance `_handle_message()` to update progress label with running count
  - Modify progress handling to show "Processing client X"
  - On complete message, show final count
- **Pattern**: Reference `gui.py:320-337` for message handling
- **Depends on**: Task 6
- **Validate**: Manual GUI test

### Task 8: ADD total clients counter

- **Action**: UPDATE
- **Implement**: After loop completes, show total in status
  - Track start time and end time
  - Calculate and display stats: "Completed 15 clients in 12 minutes"
- **Pattern**: Reference `gui.py:335-337` for complete handling
- **Depends on**: Task 5, Task 7
- **Validate**: Manual E2E test

## Testing Requirements

Tests to be written during /execute:

- [ ] Unit test: `state.py` ClientTracker - mark, check, clear
- [ ] Unit test: `sounds.py` play_iteration - doesn't crash
- [ ] Integration test: `vision.find_next_client()` with processed set (mock)
- [ ] E2E test: Loop mode with 3+ clients in TaxAct

**Test Levels**: Unit tests for state.py and sounds.py, E2E for full loop

## Bug Handling

During implementation:
- Bugs caused by THESE changes → Fix immediately
- Pre-existing bugs discovered → Document in `.agents/bugs/`, do NOT fix
- NEVER modify working code outside the scope of this plan

## Rollback Strategy

If implementation fails:
1. `git stash` or `git checkout .` to revert changes
2. Delete `clickbot/state.py` if created
3. Restore original `bot_controller.py`, `vision.py`, `sounds.py`, `gui.py`

## Manual Verification

After implementation, manually verify:
- [ ] Start bot with 3+ clients with empty Fed EF Status
- [ ] Bot processes first client, returns to Client Manager
- [ ] Windows notification sound plays before second client
- [ ] Bot continues to second client automatically
- [ ] Bot stops when no more unprocessed clients
- [ ] GUI shows progress: "Processing client 2", "Processing client 3"
- [ ] Final status shows: "Completed X clients"
- [ ] Stop button works during loop (stops after current iteration)
- [ ] If a client fails: Bot skips it and continues

## Notes

- **Scroll in Client List**: The table scroll coordinates (400, 500) are estimates. May need calibration with real TaxAct.
- **Error Recovery**: Errors skip the current client but don't stop the bot. This is intentional per user request.
- **No Persistence**: State is in-memory only. Restarting the bot clears the processed list. This is MVP-scope per PRD.
