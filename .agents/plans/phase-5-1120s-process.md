# Plan: Phase 5 - 1120S Process File

## User Story

Als Steuerberater möchte ich, dass der Bot automatisch Form 1120S Clients verarbeitet, damit ich beide Return-Types (1120 und 1120S) im Loop-Modus ohne manuelle Intervention bearbeiten kann.

## Acceptance Criteria

- [ ] `config/processes/1120S.json` existiert mit vollständiger Schrittdefinition
- [ ] Gemeinsame Buttons in `common/` verschoben und 1120.json aktualisiert
- [ ] Bot kann 1120S Client komplett durchlaufen (18 Schritte)
- [ ] Error-Handling für Alerts implementiert (wie bei 1120)
- [ ] Scroll auf Extension Payment Screen funktioniert

## Context

Phase 5 erstellt die Prozess-Definition für Form 1120S E-File Extensions. Der 1120S-Flow ist einfacher als 1120 (18 vs 40 Schritte) - keine Form 7004 Screens, keine Officer-Felder, keine Checkbox-Screens. Zwei Buttons werden von `1120/` nach `common/` refactored da sie in beiden Flows verwendet werden.

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `config/processes/1120.json` | Pattern für Prozess-Definition | 1-410 |
| `clickbot/process_executor.py` | Führt Steps aus | alle |
| `clickbot/vision.py` | Template Matching | `find_element()` |

### Patterns to Follow
- Step-Struktur aus `1120.json:12-28` (id, name, action, target, wait_after)
- Conditional-Pattern aus `1120.json:326-344` (element_visible check)
- Scroll-Pattern aus `1120.json:183-196` (scroll_until_visible)

## Dependencies

- **New Packages**: none
- **Affected Modules**: process_loader.py (lädt neue JSON), 1120.json (Pfad-Updates)
- **Breaking Changes**: Nein (Pfade in 1120.json werden aktualisiert)

## Tasks

### Task 1: REFACTOR `assets - move buttons to common`

- **Action**: REFACTOR
- **Implement**:
  - Verschiebe `.agents/screenshots/buttons/1120/submit_efile.png` → `.agents/screenshots/buttons/common/submit_efile.png`
  - Verschiebe `.agents/screenshots/buttons/1120/popup_add_remove_states.png` → `.agents/screenshots/buttons/common/popup_add_remove_states.png`
- **Pattern**: Bestehende Struktur in `common/`
- **Depends on**: none
- **Validate**: `dir .agents\screenshots\buttons\common\submit_efile.png`

### Task 2: UPDATE `config/processes/1120.json`

- **Action**: UPDATE
- **Implement**: Aktualisiere Pfade für verschobene Buttons:
  - `"1120/submit_efile.png"` → `"common/submit_efile.png"` (Zeile 352, 356)
  - `"1120/popup_add_remove_states.png"` → `"common/popup_add_remove_states.png"` (Zeile 20)
- **Pattern**: Bestehende common-Referenzen in 1120.json
- **Depends on**: Task 1
- **Validate**: `findstr "common/submit_efile" config\processes\1120.json`

### Task 3: CREATE `config/processes/1120S.json`

- **Action**: CREATE
- **Implement**: Erstelle komplette Prozess-Definition mit 18 Schritten:

```json
{
  "name": "Form 1120S E-File Extension",
  "return_type": "1120S",
  "version": "1.0",
  "description": "Automated E-File Extension process for Form 1120-S (S Corporation)",
  "static_inputs": {},
  "steps": [
    // Step 1: Close Add/Remove States popup if present
    // Step 2: Click E-file menu
    // Step 3: Click Submit Electronic Filing
    // Step 4: Select File Extension option
    // Step 5: Click Continue (Filing)
    // Step 6-13: Click Continue (8x für diverse Screens)
    // Step 14: Scroll on Extension Payment + Continue
    // Step 15: Click Start Alerts
    // Step 16: Handle Alerts Result (conditional)
    // Step 17: Click Submit E-file (conditional)
    // Step 18: Click Continue after submit (conditional)
    // Step 19: Click Continue (State Extension)
    // Step 20: Click New Return
    // Step 21: Close Add Client popup
  ]
}
```

Vollständige Step-Details siehe Implementation unten.

- **Pattern**: `config/processes/1120.json:1-410`
- **Depends on**: Task 1, Task 2
- **Validate**: `python -c "import json; json.load(open('config/processes/1120S.json'))"`

## Task 3 - Detaillierte Step-Implementierung

```json
{
  "name": "Form 1120S E-File Extension",
  "return_type": "1120S",
  "version": "1.0",
  "description": "Automated E-File Extension process for Form 1120-S (S Corporation) - 100% screenshot-based",
  "static_inputs": {},
  "steps": [
    {
      "id": 1,
      "name": "close_popup_if_present",
      "action": "conditional",
      "description": "Close Add/Remove State popup if it appears",
      "condition": {
        "type": "element_visible",
        "image": "common/popup_add_remove_states.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "common/popup_close_x.png" }
      },
      "if_false": "continue",
      "wait_after": 1.0
    },
    {
      "id": 2,
      "name": "click_efile_menu",
      "action": "click",
      "description": "Click E-File in the top menu bar",
      "target": { "image": "common/efile_menu.png" },
      "wait_after": 1.0
    },
    {
      "id": 3,
      "name": "click_submit_electronic_filing",
      "action": "click",
      "description": "Select Submit Electronic Filing Return in popup",
      "target": { "image": "common/submit_electronic_filing.png" },
      "wait_after": 1.0
    },
    {
      "id": 4,
      "name": "select_file_extension",
      "action": "click",
      "description": "Select File Extension option",
      "target": { "image": "common/file_extension_option_unchecked.png" },
      "wait_after": 1.0
    },
    {
      "id": 5,
      "name": "click_continue_filing",
      "action": "click",
      "description": "Click Continue on Filing screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 1.0
    },
    {
      "id": 6,
      "name": "click_continue_extension_intro",
      "action": "click",
      "description": "Continue on Extension Intro screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 1.0
    },
    {
      "id": 7,
      "name": "click_continue_s_corp_name",
      "action": "click",
      "description": "Continue on S Corporation Name screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 1.0
    },
    {
      "id": 8,
      "name": "click_continue_address",
      "action": "click",
      "description": "Continue on Address screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 1.0
    },
    {
      "id": 9,
      "name": "click_continue_ein",
      "action": "click",
      "description": "Continue on EIN screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 1.0
    },
    {
      "id": 10,
      "name": "click_continue_calendar_year",
      "action": "click",
      "description": "Continue on Calendar Year screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 1.0
    },
    {
      "id": 11,
      "name": "click_continue_who_signing",
      "action": "click",
      "description": "Continue on Who is Signing screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 1.0
    },
    {
      "id": 12,
      "name": "click_continue_ero_statement",
      "action": "click",
      "description": "Continue on ERO Statement screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 1.0
    },
    {
      "id": 13,
      "name": "click_continue_email_notification",
      "action": "click",
      "description": "Continue on Email Notification screen",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 1.0
    },
    {
      "id": 14,
      "name": "scroll_extension_payment",
      "action": "scroll_until_visible",
      "description": "Scroll down on Extension Payment screen until Continue visible",
      "target": {
        "image": "common/continue_blue.png",
        "scroll_x": 960,
        "scroll_y": 540,
        "scroll_direction": "down",
        "max_scrolls": 5
      },
      "wait_after": 1.0
    },
    {
      "id": 15,
      "name": "click_continue_extension_payment",
      "action": "click",
      "description": "Continue on Extension Payment screen (after scroll)",
      "target": { "image": "common/continue_blue.png" },
      "wait_after": 1.0
    },
    {
      "id": 16,
      "name": "click_start_alerts",
      "action": "click",
      "description": "Click Start Alerts button",
      "target": { "image": "common/start_alerts.png" },
      "wait_after": 1.5
    },
    {
      "id": 17,
      "name": "handle_alerts_result",
      "action": "conditional",
      "description": "Check if 'You're Good to Go' or error - different actions",
      "condition": {
        "type": "element_visible",
        "image": "common/passed_alerts.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "common/continue_blue.png" }
      },
      "if_false": {
        "action": "click",
        "description": "Click Clients button to return (Error case)",
        "target": { "image": "common/clients_button.png" }
      },
      "wait_after": 1.0
    },
    {
      "id": 18,
      "name": "click_submit_efile",
      "action": "conditional",
      "description": "Click Submit E-File button if visible",
      "condition": {
        "type": "element_visible",
        "image": "common/submit_efile.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "common/submit_efile.png" }
      },
      "if_false": "continue",
      "wait_after": 1.0
    },
    {
      "id": 19,
      "name": "click_continue_done",
      "action": "conditional",
      "description": "Click Continue on Done screen if visible",
      "condition": {
        "type": "element_visible",
        "image": "common/continue_blue.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "common/continue_blue.png" }
      },
      "if_false": "continue",
      "wait_after": 1.0
    },
    {
      "id": 20,
      "name": "click_continue_state_extension",
      "action": "conditional",
      "description": "Click Continue on State Extension question if visible",
      "condition": {
        "type": "element_visible",
        "image": "common/continue_blue.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "common/continue_blue.png" }
      },
      "if_false": "continue",
      "wait_after": 1.0
    },
    {
      "id": 21,
      "name": "click_new_return",
      "action": "conditional",
      "description": "Click New Return button (Filing Complete screen)",
      "condition": {
        "type": "element_visible",
        "image": "common/new_return.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "common/new_return.png" }
      },
      "if_false": "continue",
      "wait_after": 1.0
    },
    {
      "id": 22,
      "name": "close_add_client_popup",
      "action": "conditional",
      "description": "Close Add Client popup if present",
      "condition": {
        "type": "element_visible",
        "image": "common/popup_close_x.png"
      },
      "if_true": {
        "action": "click",
        "target": { "image": "common/popup_close_x.png" }
      },
      "if_false": "continue",
      "wait_after": 1.0
    }
  ]
}
```

## Testing Requirements

- [ ] JSON-Syntax valide (python json.load)
- [ ] Alle referenzierten Button-Images existieren
- [ ] 1120.json funktioniert noch nach Pfad-Update
- [ ] E2E: 1120S Client komplett durchlaufen

**Test Levels**: Integration (JSON loading) + E2E (gegen TaxAct)

## Bug Handling

- Bugs durch DIESE Änderungen → Sofort fixen
- Vorher existierende Bugs → Dokumentieren in `.agents/bugs/`, NICHT fixen
- NIEMALS funktionierenden Code außerhalb dieses Plans ändern

## Rollback Strategy

1. `git checkout .` um alle Änderungen rückgängig zu machen
2. Falls Buttons bereits verschoben: `git checkout .agents/screenshots/buttons/`

## Manual Verification

Nach Implementation manuell prüfen:
- [ ] Bot mit 1120 Client starten - läuft komplett durch
- [ ] Bot mit 1120S Client starten - läuft komplett durch
- [ ] Error-Fall testen: Client mit fehlenden Daten (sollte zu Clients zurückkehren)

## Notes

- 1120S ist **einfacher** als 1120: Keine Officer-Felder, keine Checkboxen
- Steps 17-22 sind alle conditional, da nach Error der Flow abgekürzt wird
- Der Bot erkennt den Return-Type automatisch via OCR (Phase 4 bereits implementiert)
- `static_inputs` ist leer, da 1120S keine Felder zum Ausfüllen hat
