# Plan: 1120 Process Redesign + Client-Open Polling

## User Story

Als Steuerberater möchte ich, dass der 1120-Prozess technisch auf dem gleichen Niveau wie 1040 ist (Screen-Verifikation, Abort-Handling, Locked-Client-Support, dynamisches Polling), damit der Bot zuverlässig und fehlertolerant arbeitet.

## Acceptance Criteria

- [ ] `1120.json` hat 26 Stages mit `verify_screen`/`verify_next` (wie 1040)
- [ ] Abort-Handling mit spezifischen `abort_reason` für Wizard, Alerts, Submit
- [ ] Locked-Client-Handling in Stage 4 (Filing)
- [ ] Checkbox-Stages als `multi` konsolidiert (Homeowners, No Office, Section)
- [ ] Officer-Felder + PIN als `multi` mit `type_field`
- [ ] `no_retry: true` + `verify_timeout: 30` auf Submit-Stage
- [ ] Bot wartet dynamisch (bis 60s) nach Doppelklick statt fest 4s
- [ ] Alle 26 Verify-Screenshots in `assets/verify/1120/` werden korrekt referenziert
- [ ] Bestehende 1040- und 1120S-Prozesse bleiben funktional
- [ ] SSN/EIN-Normalisierung formatiert return-type-abhängig: SSN `XXX-XX-XXXX` (1040) vs. EIN `XX-XXXXXXX` (1120/1120S)

## Context

Der 1120-Prozess verwendet das alte `steps`-Format (40 flache Steps ohne Screen-Verifikation). Dieser Plan schreibt `1120.json` komplett neu im 1040-Pattern (26 konsolidierte Stages mit `verify_screen`, `verify_next`, Abort-Handling, Locked-Client-Support). Zusätzlich wird `bot_controller.py` geändert, um nach dem Doppelklick auf einen Client dynamisch auf den Form-View zu pollen statt 4 Sekunden fest zu warten.

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `config/processes/1040.json` | Referenz-Implementation (19 Stages, 1040-Pattern) | komplett |
| `config/processes/1120.json` | Zu ersetzendes Legacy-Format (40 Steps) | komplett |
| `config/processes/1120S.json` | Bestehendes Stages-Format (20 Stages) | komplett |
| `clickbot/bot_controller.py` | Doppelklick mit 4s-Wait | Zeile 334 |
| `clickbot/process_executor.py` | Unterstützt bereits ALLE nötigen Features | Zeilen 354-511 (conditional/abort), 621-739 (verify) |
| `clickbot/vision.py` | SSN/EIN-Normalisierung hardcoded auf XXX-XX-XXXX | Zeilen 897-903, 954-958, 1006-1011 |
| `clickbot/process_loader.py` | Lädt Prozess-JSON, unterstützt `stages` + `steps` | Zeilen 30-61 |
| `clickbot/vision.py` | `wait_for_element()` für Polling | Zeile 270 |

### Patterns to Follow

**1040.json Stage-Pattern** (alle Stages folgen diesem Schema):
```json
{
    "id": 1,
    "name": "click_efile_menu",
    "description": "Click E-File in the top menu bar",
    "verify_screen": "1040/01_basic_information.png",
    "action": "click",
    "target": { "image": "common/efile_menu.png" },
    "verify_next": "1040/02_efile_center.png"
}
```

**1040 Abort-Pattern** (Stage 12, `process_executor.py:454-464`):
```json
"if_false": {
    "abort": true,
    "abort_reason": "FAIL: Wizard (Stage 12)",
    "actions": [
        { "action": "click", "target": { "image": "common/clients_button.png", "search_region": [0, 0, 300, 80] }, "wait_after": 1.5 },
        { "action": "conditional", "condition": { "type": "element_visible", "image": "common/blue_questionmark_icon.png", "search_region": [800, 530, 50, 70] }, "if_true": { "action": "click", "target": { "image": "1040/no_default.png", "search_region": [955, 615, 80, 30] } }, "if_false": "continue", "wait_after": 3.0 }
    ]
}
```

**1040 Locked-Client-Pattern** (Stage 3 multi):
```json
{
    "action": "conditional",
    "condition": { "type": "element_visible", "image": "common/locked_2.png", "timeout": 3.0 },
    "if_true": { "action": "click", "target": { "image": "common/unlock_and_save.png" } },
    "if_false": "continue",
    "wait_after": 1.0
}
```

**Bot-Controller Doppelklick** (`bot_controller.py:334`):
```python
executor.double_click(click_pos[0], click_pos[1], wait=4.0)  # Hardcoded 4s
```

### Existing Button Templates (`.agents/screenshots/buttons/1120/`)
- `complete_form_7004.png`, `efile_form_7004.png`, `start_form_7004_alerts.png`
- `label_title.png`, `label_email.png`, `label_phone.png`, `label_pin.png`
- `checkbox_homeowners_checked.png`, `checkbox_homeowners_unchecked.png`
- `checkbox_no_office_checked.png`, `checkbox_no_office_unchecked.png`
- `checkbox_section_checked.png`, `checkbox_section_unchecked.png`

### Existing Verify Templates (`assets/verify/1120/`)
26 Screenshots: `01_form_view.png` bis `26_base.png` — alle vorhanden.

## Dependencies

- **New Packages**: none
- **Affected Modules**: `config/processes/1120.json` (rewrite), `clickbot/bot_controller.py` (polling), `clickbot/vision.py` (SSN/EIN-Format), `config/processes/1040.json` (1 Zeile), `config/processes/1120S.json` (1 Zeile)
- **Breaking Changes**: Nein — `process_executor.py` unterstützt bereits alle Features, `process_loader.py` unterstützt `stages`

## Tasks

### Task 1: CREATE `config/processes/1120.json` (Rewrite)

- **Action**: CREATE (ersetzt bestehende Datei)
- **Implement**: Komplett neues 26-Stage JSON im 1040-Pattern. Struktur:

**Stage 1 — Close popup if present (conditional)**
```json
{
    "id": 1, "name": "close_popup_if_present",
    "description": "Close Add/Remove State popup if it appears",
    "action": "conditional",
    "condition": { "type": "element_visible", "image": "common/popup_add_remove_states.png" },
    "if_true": { "action": "click", "target": { "image": "common/popup_close_x.png" } },
    "if_false": "continue",
    "wait_after": 1.0
}
```
Kein `verify_screen` (Popup kann erscheinen oder nicht). Kein `verify_next` (nächster Stage verifiziert).

**Stage 2 — Click E-File menu**
```json
{
    "id": 2, "name": "click_efile_menu",
    "description": "Click E-File in the top menu bar",
    "verify_screen": "1120/01_form_view.png",
    "action": "click",
    "target": { "image": "common/efile_menu.png" },
    "verify_next": "1120/02_efile_center.png"
}
```

**Stage 3 — Click Submit Electronic Filing**
```json
{
    "id": 3, "name": "click_submit_electronic_filing",
    "description": "Select Submit Electronic Filing Return in popup",
    "verify_screen": "1120/02_efile_center.png",
    "action": "click",
    "target": { "image": "common/submit_electronic_filing.png" },
    "verify_next": "1120/03_filing.png"
}
```

**Stage 4 — File Extension + Continue + locked_2 (multi)**
Pattern: 1040 Stage 3. Checkbox conditional + Continue + locked_2 polling.
```json
{
    "id": 4, "name": "select_file_extension_and_continue",
    "description": "Check File Extension (if unchecked), click Continue, handle locked_2 popup if present",
    "verify_screen": "1120/03_filing.png",
    "action": "multi",
    "actions": [
        {
            "action": "conditional",
            "condition": { "type": "element_visible", "image": "common/file_extension_option_unchecked.png" },
            "if_true": { "action": "click", "target": { "image": "common/file_extension_option_unchecked.png" } },
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
            "condition": { "type": "element_visible", "image": "common/locked_2.png", "timeout": 3.0 },
            "if_true": { "action": "click", "target": { "image": "common/unlock_and_save.png" } },
            "if_false": "continue",
            "wait_after": 1.0
        }
    ],
    "verify_next": "1120/04_federal_extension.png"
}
```

**Stage 5 — Click Yes Federal Extension**
```json
{
    "id": 5, "name": "click_yes_federal_extension",
    "description": "Click Yes on Federal Extension screen",
    "verify_screen": "1120/04_federal_extension.png",
    "action": "click",
    "target": { "image": "common/yes_green.png" },
    "verify_next": "1120/05_form_7004_application.png"
}
```

**Stage 6 — Click Complete Form 7004**
```json
{
    "id": 6, "name": "click_complete_form_7004",
    "description": "Click Complete Form 7004 button",
    "verify_screen": "1120/05_form_7004_application.png",
    "action": "click",
    "target": { "image": "1120/complete_form_7004.png" },
    "verify_next": "1120/06_corporation_name.png"
}
```

**Stage 7 — Continue Corporation Name**
```json
{
    "id": 7, "name": "click_continue_corporation_name",
    "description": "Continue on Corporation Name screen",
    "verify_screen": "1120/06_corporation_name.png",
    "action": "click",
    "target": { "image": "common/continue_blue.png" },
    "verify_next": "1120/07_homeowners.png"
}
```

**Stage 8 — Homeowners: checkbox + Continue (multi)**
Konsolidiert alte Steps 9+10. Pattern: checkbox_checked condition + continue.
```json
{
    "id": 8, "name": "handle_homeowners_and_continue",
    "description": "Ensure Homeowners checkbox unchecked, then Continue",
    "verify_screen": "1120/07_homeowners.png",
    "action": "multi",
    "actions": [
        {
            "action": "conditional",
            "condition": {
                "type": "checkbox_checked",
                "image_checked": "1120/checkbox_homeowners_checked.png",
                "image_unchecked": "1120/checkbox_homeowners_unchecked.png"
            },
            "if_true": { "action": "click_detected" },
            "if_false": "continue",
            "wait_after": 0.5
        },
        {
            "action": "click",
            "target": { "image": "common/continue_blue.png" }
        }
    ],
    "verify_next": "1120/08_address.png"
}
```

**Stage 9 — Continue Address**
```json
{
    "id": 9, "name": "click_continue_address",
    "description": "Continue on Address screen",
    "verify_screen": "1120/08_address.png",
    "action": "click",
    "target": { "image": "common/continue_blue.png" },
    "verify_next": "1120/09_federal_id.png"
}
```

**Stage 10 — Continue Federal ID**
```json
{
    "id": 10, "name": "click_continue_federal_id",
    "description": "Continue on Federal ID Number screen",
    "verify_screen": "1120/09_federal_id.png",
    "action": "click",
    "target": { "image": "common/continue_blue.png" },
    "verify_next": "1120/10_fiscal_year.png"
}
```

**Stage 11 — Continue Fiscal Year**
```json
{
    "id": 11, "name": "click_continue_fiscal_year",
    "description": "Continue on Fiscal Year screen",
    "verify_screen": "1120/10_fiscal_year.png",
    "action": "click",
    "target": { "image": "common/continue_blue.png" },
    "verify_next": "1120/11_todays_date.png"
}
```

**Stage 12 — Continue Today's Date**
```json
{
    "id": 12, "name": "click_continue_todays_date",
    "description": "Continue on Today's Date screen",
    "verify_screen": "1120/11_todays_date.png",
    "action": "click",
    "target": { "image": "common/continue_blue.png" },
    "verify_next": "1120/12_no_office.png"
}
```

**Stage 13 — No Office: checkbox + Continue (multi)**
Konsolidiert alte Steps 15+16. Gleiche checkbox_checked Pattern wie Stage 8.
```json
{
    "id": 13, "name": "handle_no_office_and_continue",
    "description": "Ensure No Office checkbox unchecked, then Continue",
    "verify_screen": "1120/12_no_office.png",
    "action": "multi",
    "actions": [
        {
            "action": "conditional",
            "condition": {
                "type": "checkbox_checked",
                "image_checked": "1120/checkbox_no_office_checked.png",
                "image_unchecked": "1120/checkbox_no_office_unchecked.png"
            },
            "if_true": { "action": "click_detected" },
            "if_false": "continue",
            "wait_after": 0.5
        },
        {
            "action": "click",
            "target": { "image": "common/continue_blue.png" }
        }
    ],
    "verify_next": "1120/13_section.png"
}
```

**Stage 14 — Section 1.6081-5: checkbox + Continue (multi)**
Konsolidiert alte Steps 17+18. Gleiche Pattern.
```json
{
    "id": 14, "name": "handle_section_and_continue",
    "description": "Ensure Section 1.6081-5 checkbox unchecked, then Continue",
    "verify_screen": "1120/13_section.png",
    "action": "multi",
    "actions": [
        {
            "action": "conditional",
            "condition": {
                "type": "checkbox_checked",
                "image_checked": "1120/checkbox_section_checked.png",
                "image_unchecked": "1120/checkbox_section_unchecked.png"
            },
            "if_true": { "action": "click_detected" },
            "if_false": "continue",
            "wait_after": 0.5
        },
        {
            "action": "click",
            "target": { "image": "common/continue_blue.png" }
        }
    ],
    "verify_next": "1120/14_tax_liability.png"
}
```

**Stage 15 — Tax Liability: scroll + Continue (multi)**
Konsolidiert alte Steps 19+20. Pattern: scroll_until_visible + click.
```json
{
    "id": 15, "name": "scroll_and_continue_tax_liability",
    "description": "Scroll down on Tax Liability screen, then Continue",
    "verify_screen": "1120/14_tax_liability.png",
    "action": "multi",
    "actions": [
        {
            "action": "scroll_until_visible",
            "target": {
                "image": "common/continue_blue.png",
                "scroll_x": 960, "scroll_y": 540,
                "scroll_direction": "down", "max_scrolls": 10
            },
            "wait_after": 0.5
        },
        {
            "action": "click",
            "target": { "image": "common/continue_blue.png" }
        }
    ],
    "verify_next": "1120/15_payment_amount.png"
}
```

**Stage 16 — Continue Payment Amount**
```json
{
    "id": 16, "name": "click_continue_payment_amount",
    "description": "Continue on Payment Amount screen",
    "verify_screen": "1120/15_payment_amount.png",
    "action": "click",
    "target": { "image": "common/continue_blue.png" },
    "verify_next": "1120/16_print_form.png"
}
```

**Stage 17 — Click E-File Form 7004**
Kein `verify_next` — Ergebnis unvorhersehbar (Acknowledgement ODER Wizard). `wait_after: 3.0`.
```json
{
    "id": 17, "name": "click_efile_form_7004",
    "description": "Click E-File Form 7004 button on Print screen",
    "verify_screen": "1120/16_print_form.png",
    "action": "click",
    "target": { "image": "1120/efile_form_7004.png" },
    "wait_after": 3.0
}
```

**Stage 18 — Handle Acknowledgement (conditional + abort)**
Pattern: 1040 Stage 12. Prüft ob Acknowledgement-Screen sichtbar (verify base_path). Bei Wizard → abort mit Recovery.
```json
{
    "id": 18, "name": "handle_post_efile",
    "description": "If on Acknowledgement screen, click Continue; otherwise abort (Wizard)",
    "action": "conditional",
    "condition": {
        "type": "element_visible",
        "image": "1120/17_acknowledgement.png",
        "base_path": "verify"
    },
    "if_true": {
        "action": "click",
        "target": { "image": "common/continue_blue.png" },
        "verify_next": "1120/18_officer_info.png"
    },
    "if_false": {
        "abort": true,
        "abort_reason": "FAIL: Wizard (Stage 18)",
        "description": "Bail out: click Clients, dismiss save-changes dialog",
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
                    "image": "common/blue_questionmark_icon.png",
                    "search_region": [800, 530, 50, 70]
                },
                "if_true": {
                    "action": "click",
                    "target": { "image": "1040/no_default.png", "search_region": [955, 615, 80, 30] }
                },
                "if_false": "continue",
                "wait_after": 3.0
            }
        ]
    }
}
```
**Hinweis:** Verwendet `1040/no_default.png` für den "Nein"-Button im Save-Changes-Dialog — gleicher Dialog wie bei 1040.

**Stage 19 — Officer Info: fill 4 fields + Continue (multi)**
Konsolidiert alte Steps 24-30. Verwendet `type_field` (Clipboard-Check: nur tippen wenn leer).
```json
{
    "id": 19, "name": "fill_officer_info_and_continue",
    "description": "Fill Title, Email, Phone if empty, then Continue",
    "verify_screen": "1120/18_officer_info.png",
    "action": "multi",
    "actions": [
        { "action": "click", "target": { "image": "1120/label_title.png", "offset_x": 50, "offset_y": 35 }, "wait_after": 0.3 },
        { "action": "type_field", "text_key": "officer_title", "wait_after": 0.3 },
        { "action": "click", "target": { "image": "1120/label_email.png", "offset_x": 50, "offset_y": 35 }, "wait_after": 0.3 },
        { "action": "type_field", "text_key": "officer_email", "wait_after": 0.3 },
        { "action": "click", "target": { "image": "1120/label_phone.png", "offset_x": 50, "offset_y": 35 }, "wait_after": 0.3 },
        { "action": "type_field", "text_key": "officer_phone", "wait_after": 0.3 },
        { "action": "click", "target": { "image": "common/continue_blue.png" } }
    ],
    "verify_next": "1120/19_officer_signature.png"
}
```

**Stage 20 — Officer Signature: fill PIN + Continue (multi)**
Konsolidiert alte Steps 31-33.
```json
{
    "id": 20, "name": "fill_pin_and_continue",
    "description": "Fill PIN if empty, then Continue",
    "verify_screen": "1120/19_officer_signature.png",
    "action": "multi",
    "actions": [
        { "action": "click", "target": { "image": "1120/label_pin.png", "offset_x": -17, "offset_y": 35 }, "wait_after": 0.3 },
        { "action": "type_field", "text_key": "officer_pin", "wait_after": 0.3 },
        { "action": "click", "target": { "image": "common/continue_blue.png" } }
    ],
    "verify_next": "1120/20_ero_signature.png"
}
```

**Stage 21 — Continue ERO Signature**
```json
{
    "id": 21, "name": "click_continue_ero_signature",
    "description": "Continue on ERO Signature screen",
    "verify_screen": "1120/20_ero_signature.png",
    "action": "click",
    "target": { "image": "common/continue_blue.png" },
    "verify_next": "1120/21_alerts.png"
}
```

**Stage 22 — Click Start Form 7004 Alerts**
Kein `verify_next` — Ergebnis unvorhersehbar (Passed ODER Error). `wait_after: 2.0`.
```json
{
    "id": 22, "name": "click_start_alerts",
    "description": "Click Start Form 7004 Alerts button",
    "verify_screen": "1120/21_alerts.png",
    "action": "click",
    "target": { "image": "1120/start_form_7004_alerts.png" },
    "wait_after": 2.0
}
```

**Stage 23 — Handle Alerts Result (conditional + abort)**
Pattern: 1040 Stage 16. Bei Passed → Continue, sonst → abort.
```json
{
    "id": 23, "name": "handle_alerts_result",
    "description": "Check if Passed Alerts or error - abort if not passed",
    "action": "conditional",
    "condition": { "type": "element_visible", "image": "common/passed_alerts.png" },
    "if_true": {
        "action": "click",
        "target": { "image": "common/continue_blue.png" },
        "verify_next": "1120/23_submit.png"
    },
    "if_false": {
        "abort": true,
        "abort_reason": "FAIL: Alerts not passed",
        "actions": [
            {
                "action": "click",
                "target": { "image": "common/clients_button.png", "search_region": [0, 0, 300, 80] },
                "wait_after": 2.0
            }
        ]
    }
}
```

**Stage 24 — Submit E-File (no_retry, verify_timeout 30)**
Pattern: 1040 Stage 17. Safety: kein doppelter Klick.
```json
{
    "id": 24, "name": "click_submit_efile",
    "description": "Click Submit E-File button (no retry - dangerous!)",
    "verify_screen": "1120/23_submit.png",
    "action": "click",
    "target": { "image": "common/submit_efile.png" },
    "verify_next": "1120/24_successful.png",
    "no_retry": true,
    "verify_timeout": 30.0
}
```

**Stage 25 — Handle Submit Result (conditional + abort)**
Pattern: 1040 Stage 18. Prüft "E-File Successful" via verify base_path.
```json
{
    "id": 25, "name": "handle_submit_result",
    "description": "Check if E-File Successful or error - safeguard",
    "action": "conditional",
    "condition": {
        "type": "element_visible",
        "image": "1120/24_successful.png",
        "base_path": "verify"
    },
    "if_true": {
        "action": "click",
        "target": { "image": "common/continue_green.png" },
        "verify_next": "1120/25_filing_complete.png"
    },
    "if_false": {
        "abort": true,
        "abort_reason": "FAIL: Submit unsuccessful",
        "actions": [
            {
                "action": "click",
                "target": { "image": "common/clients_button.png", "search_region": [0, 0, 300, 80] },
                "wait_after": 2.0
            }
        ]
    }
}
```

**Stage 26 — Click Clients button on Filing Complete**
```json
{
    "id": 26, "name": "click_clients_complete",
    "description": "Click Clients button on Filing Complete screen to return to Client Manager",
    "verify_screen": "1120/25_filing_complete.png",
    "action": "click",
    "target": { "image": "common/clients_button.png", "search_region": [0, 0, 300, 80] },
    "verify_next": "1120/26_base.png"
}
```

Top-level Felder:
```json
{
    "name": "Form 1120 E-File Extension",
    "return_type": "1120",
    "version": "3.0",
    "description": "26-stage process with screen verification for Form 1120 (Corporation)",
    "open_verify_image": "1120/01_form_view.png",
    "static_inputs": {
        "officer_title": "president",
        "officer_email": "info@tmaccountant.com",
        "officer_phone": "(847)850-0085",
        "officer_pin": "12345"
    },
    "stages": [ ... ]
}
```

- **Pattern**: Referenz `config/processes/1040.json` (komplette Datei)
- **Depends on**: none
- **Validate**: `python -c "import json; d=json.load(open('config/processes/1120.json')); assert 'stages' in d; assert len(d['stages']) == 26; print(f'OK: {len(d[\"stages\"])} stages')"`

### Task 2: UPDATE `clickbot/bot_controller.py` — Dynamisches Polling nach Doppelklick

- **Action**: UPDATE
- **Implement**: Nach dem Doppelklick (Zeile 334) dynamisch auf den Form-View pollen statt 4s fest zu warten.

Änderung 1: Prozess vorladen um `open_verify_image` zu lesen (vor Zeile 334).
```python
# Load process to get open_verify_image for polling
from clickbot.process_loader import load_process
try:
    process_def = load_process(self.selected_return_type)
    open_verify_image = process_def.get("open_verify_image")
except Exception:
    open_verify_image = None
```

Änderung 2: Zeile 334 ersetzen — statt `wait=4.0` dynamisch pollen.
```python
# Double-click to open the client
executor.double_click(click_pos[0], click_pos[1], wait=0)

# Wait for client form to load (dynamic polling instead of fixed 4s wait)
if open_verify_image:
    verify_base = self.settings.get("validation", {}).get("verify_base_path", "assets/verify")
    # Resolve relative path
    from clickbot import paths as bot_paths
    if not Path(verify_base).is_absolute():
        verify_base = str(bot_paths.get_bundle_dir() / verify_base)

    self._send_log(f"Waiting for client to load ({open_verify_image})...")
    loaded = vision.wait_for_element(
        open_verify_image, timeout=60.0, poll_interval=0.5,
        base_path=verify_base, stop_event=self.stop_event
    )
    if loaded is None and not self.stop_event.is_set():
        self._send_log(f"Client did not load within 60s, retrying...")
        # Client didn't load — skip this client, go back to base
        sounds.play_error()
        if csv_records is not None:
            update_client_status(
                self.csv_path, client_row.client_name,
                client_row.client_id, self.selected_return_type,
                "FAIL: Client did not load"
            )
            csv_records = load_csv(self.csv_path)
        self._send_log(f"SKIPPED: {client_row.client_name} - Client did not load")
        self._recover_to_client_manager()
        continue
else:
    time.sleep(4.0)  # Fallback for processes without open_verify_image
```

Änderung 3: `load_process` Import einmalig oben oder am Anfang von `_run()` machen, nicht in der Schleife. Den process-load VOR die Hauptschleife verschieben.

- **Pattern**: Referenz `vision.wait_for_element()` bei `vision.py:270`, Verify-Base-Path-Auflösung bei `process_executor.py:607-619`
- **Depends on**: Task 1 (braucht `open_verify_image` Feld)
- **Validate**: `python -c "from clickbot.bot_controller import BotController; print('Import OK')"`

### Task 3: UPDATE `config/processes/1040.json` — `open_verify_image` hinzufügen

- **Action**: UPDATE
- **Implement**: Feld `"open_verify_image": "1040/01_basic_information.png"` nach `"static_inputs"` einfügen.
- **Depends on**: none
- **Validate**: `python -c "import json; d=json.load(open('config/processes/1040.json')); assert d['open_verify_image'] == '1040/01_basic_information.png'; print('OK')"`

### Task 4: UPDATE `config/processes/1120S.json` — `open_verify_image` hinzufügen

- **Action**: UPDATE
- **Implement**: Feld `"open_verify_image": "1120S/02_s_corp_view.png"` nach `"static_inputs"` einfügen.
  Hinweis: `02_s_corp_view.png` statt `01_popup_add_remove.png`, da der Form-View-Header auch sichtbar ist wenn der Popup erscheint (Header ist oberhalb des Popups).
- **Depends on**: none
- **Validate**: `python -c "import json; d=json.load(open('config/processes/1120S.json')); assert d['open_verify_image'] == '1120S/02_s_corp_view.png'; print('OK')"`

### Task 5: UPDATE `clickbot/vision.py` — Return-Type-abhängige SSN/EIN-Formatierung

- **Action**: UPDATE
- **Implement**: Neue Hilfsfunktion `normalize_ssn_ein()` erstellen und an 3 Stellen einsetzen.

Neue Funktion (nach `normalize_return_type()`, ca. Zeile 680):
```python
def normalize_ssn_ein(raw_value: str, return_type: str = "") -> str:
    """Normalize OCR-read SSN/EIN to correct format.

    Strips non-digit characters, pads 8-digit values with leading zero,
    then formats based on return type:
    - 1040 (SSN): XXX-XX-XXXX (3-2-4)
    - 1120/1120S (EIN): XX-XXXXXXX (2-7)

    Args:
        raw_value: Raw OCR result for SSN/EIN
        return_type: Return type to determine format ("1040", "1120", "1120S")

    Returns:
        Formatted SSN/EIN string, or raw digits if length != 9
    """
    digits = re.sub(r"[^0-9]", "", raw_value)
    if len(digits) == 8:
        digits = "0" + digits
    if len(digits) != 9:
        return raw_value  # Can't format, return as-is
    if return_type == "1040":
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"  # XXX-XX-XXXX
    else:
        return f"{digits[:2]}-{digits[2:]}"  # XX-XXXXXXX (1120, 1120S, default)
```

Stelle 1 — `read_all_rows_from_screenshot()` (Zeile 897-903):
Ersetzen:
```python
# Normalize SSN/EIN to XXX-XX-XXXX format (strip non-digits, fix leading zero)
ssn_ein = cell_values[1]
digits = re.sub(r"[^0-9]", "", ssn_ein)
if len(digits) == 8:
    digits = "0" + digits
if len(digits) == 9:
    ssn_ein = f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
```
Mit:
```python
ssn_ein = normalize_ssn_ein(cell_values[1], normalize_return_type(cell_values[2]))
```
Hinweis: `cell_values[2]` ist der Return-Type der Zeile. Über `normalize_return_type()` erst den Return-Type normalisieren, dann für die EIN/SSN-Formatierung verwenden.

Stelle 2 — `scan_visible_clients_csv()` CSV-Key-Normalisierung (Zeile 952-958):
Ersetzen:
```python
csv_id = r.client_id
id_digits = re.sub(r"[^0-9]", "", csv_id)
if len(id_digits) == 8:
    id_digits = "0" + id_digits
if len(id_digits) == 9:
    csv_id = f"{id_digits[:3]}-{id_digits[3:5]}-{id_digits[5:]}"
```
Mit:
```python
csv_id = normalize_ssn_ein(r.client_id, r.return_type)
```

Stelle 3 — `scan_visible_clients_csv()` OCR-Normalisierung (Zeile 1005-1011):
Ersetzen:
```python
ssn_ein = _crop_and_ocr("ssn_ein", row_y)
# Normalize SSN/EIN to XXX-XX-XXXX format (strip non-digits, fix leading zero)
digits = re.sub(r"[^0-9]", "", ssn_ein)
if len(digits) == 8:
    digits = "0" + digits
if len(digits) == 9:
    ssn_ein = f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
```
Mit:
```python
ssn_ein = normalize_ssn_ein(_crop_and_ocr("ssn_ein", row_y), selected_return_type)
```

- **Pattern**: Gleiche Logik wie bestehende Normalisierung, nur in Funktion extrahiert und Return-Type-abhängig
- **Depends on**: none
- **Validate**: `python -c "from clickbot.vision import normalize_ssn_ein; assert normalize_ssn_ein('993871200', '1120') == '99-3871200'; assert normalize_ssn_ein('123456789', '1040') == '123-45-6789'; print('OK')"`

### Task 6: UPDATE Unit Tests

- **Action**: UPDATE
- **Implement**: Tests für die neuen Features:
  1. `1120.json` Validierung: 26 Stages, alle haben `id`/`name`/`action`, Stages mit `verify_screen` referenzieren existierende Dateien
  2. `1120.json` Abort-Stages: Stages 18, 23, 25 haben korrektes Abort-Pattern
  3. `1120.json` Multi-Stages: Stages 4, 8, 13, 14, 15, 19, 20 sind `multi` mit korrekten Sub-Actions
  4. `1120.json` Officer-Info: Stage 19 hat 4 `type_field` Actions mit korrekten `text_key` Werten
  5. `bot_controller.py`: `open_verify_image` Polling (mock `vision.wait_for_element`)
  6. Alle drei Prozesse haben `open_verify_image` Feld
  7. `normalize_ssn_ein()`: SSN-Format für 1040, EIN-Format für 1120/1120S, Leading-Zero-Padding, Non-9-Digit-Fallback
- **Pattern**: Referenz bestehende Tests in `tests/`
- **Depends on**: Tasks 1-5
- **Validate**: `pytest tests/ -v`

## Testing Requirements

- [ ] `1120.json` lädt ohne Fehler via `process_loader.load_process("1120")`
- [ ] Alle 26 Stages haben gültige `id`, `name`, `action`
- [ ] Verify-Screenshots existieren für alle referenzierten Pfade
- [ ] Abort-Stages (18, 23, 25) haben `abort: true` + `abort_reason`
- [ ] Multi-Stages (4, 8, 13, 14, 15, 19, 20) haben `actions` Array
- [ ] `static_inputs` enthält `officer_title`, `officer_email`, `officer_phone`, `officer_pin`
- [ ] `open_verify_image` existiert in allen drei Prozess-JSONs
- [ ] Bot-Controller pollt nach Doppelklick (mock-basiert)
- [ ] Edge case: `open_verify_image` fehlt → Fallback auf 4s Wait
- [ ] `normalize_ssn_ein("993871200", "1120")` → `"99-3871200"` (EIN-Format)
- [ ] `normalize_ssn_ein("123456789", "1040")` → `"123-45-6789"` (SSN-Format)
- [ ] `normalize_ssn_ein("93871200", "1120")` → `"09-3871200"` (8-Digit Leading-Zero + EIN)
- [ ] `normalize_ssn_ein("23456789", "1040")` → `"023-45-6789"` (8-Digit Leading-Zero + SSN)
- [ ] Edge case: `normalize_ssn_ein("abc", "1120")` → `"abc"` (nicht 9 Digits → raw zurück)

## Bug Handling

- Bugs durch DIESE Änderungen → sofort fixen
- Vorhandene Bugs → dokumentieren in `.agents/bugs/`, NICHT fixen
- KEIN Code außerhalb des Scopes ändern

## Rollback Strategy

1. `git stash` oder `git checkout .` zum Zurücksetzen
2. Alte `1120.json` wird durch git history wiederhergestellt
3. `bot_controller.py` Änderung ist backward-kompatibel (Fallback auf 4s)

## Manual Verification

- [ ] 1120-Client in TaxAct öffnen → Bot durchläuft alle 26 Stages
- [ ] Locked-Client testen → Stage 4 handled korrekt
- [ ] Langsamer Client-Load → Bot wartet geduldig (bis 60s)
- [ ] Alerts-Fehler → sauberer Abort mit "FAIL: Alerts not passed" in CSV
- [ ] 1040-Prozess weiterhin funktional
- [ ] 1120S-Prozess weiterhin funktional

## Notes

- `process_executor.py` wird NICHT geändert — alle Features sind bereits implementiert
- `vision.py` wird NUR für `normalize_ssn_ein()` geändert — keine Änderungen an find_element, wait_for_element etc.
- Der Save-Changes-Dialog bei Wizard-Abort verwendet `1040/no_default.png` — der "Nein"-Button sieht in allen Prozessen gleich aus. Falls nötig, kann später ein `common/no_default.png` erstellt werden.
- Die Checkbox-Stages (8, 13, 14) verwenden `checkbox_checked` Condition-Typ (wie das alte 1120.json), da die Templates bereits existieren. Alternativ hätte man `element_visible` verwenden können (wie 1040), aber `checkbox_checked` ist robuster für Checkboxen.
- Für 1120S: `open_verify_image` zeigt auf `02_s_corp_view.png` (nicht den Popup), da der Form-View-Header oberhalb des Popups sichtbar bleibt.

## Confidence Score: 9/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 10 | 1040.json ist exakte Referenz, jede Stage hat Vorlage |
| **External Knowledge** | 10 | Alles im Codebase vorhanden, keine externen Abhängigkeiten |
| **Risk** | 8 | Nur 1120.json ist neu — executor/vision bleiben unverändert. Risiko: Template-Matching für neue Verify-Screenshots könnte Confidence-Probleme haben |
| **Dependencies** | 8 | 3 Dateien geändert (bot_controller, vision, 1120.json), 2 Dateien minimal geändert (1040, 1120S) |
| **Clarity** | 9 | Jede Stage exakt spezifiziert, Abort-Pattern bekannt |
| **Testability** | 8 | JSON-Validierung per Unit-Test, E2E nur mit echtem TaxAct |

**Overall: 9/10** — Alle Patterns existieren in 1040, process_executor unterstützt bereits alles, keine Code-Änderungen am Execution-Layer nötig. Einziges Restrisiko: Verify-Screenshot-Matching bei unterschiedlichen Client-Daten.
