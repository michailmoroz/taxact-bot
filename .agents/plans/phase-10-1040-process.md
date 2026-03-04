# Plan: 1040 Prozess + Ctrl+Home Scroll-to-Top

## User Story

Als Steuerberater möchte ich Form 1040 E-File Extensions automatisieren und nach jeder Iteration zuverlässig zum Anfang der Clientliste springen, damit der Bot auch bei tausenden Clients korrekt funktioniert.

## Acceptance Criteria

- [ ] Bot verarbeitet 1040-Clients (via GUI-Auswahl) und führt den 1040-Prozess aus
- [ ] 19 Stages mit Screen-Verifikation (verify_screen/verify_next)
- [ ] Third-Party Designee Sub-Flow (konditional): 3 Felder auf einem Screen füllen
- [ ] Alerts-Ergebnis konditional: passed → weiter, sonst → Clients-Button
- [ ] Submit-Safeguard: successful → weiter, sonst → Clients-Button
- [ ] Scroll-to-Top via `Ctrl+Home` (US-Tastatur) nach jeder Iteration
- [ ] Alle bestehenden Tests weiterhin grün

## Context

Der 1040-Prozess ist ähnlich wie 1120S — eine Sequenz von ~19 Klicks mit zwei konditionalen Abzweigungen (Third-Party Designee und Alerts-Ergebnis). Das bestehende Framework unterstützt alle benötigten Actions. Zusätzlich wird der bisherige `executor.scroll(9999)` Scroll-to-Top durch `Ctrl+Home` ersetzt, das auf der US-Tastatur des Remote-PCs nach der Iteration zuverlässig funktioniert.

## Prerequisites (Screenshots — User liefert diese)

**Bevor `/execute` gestartet wird, müssen alle Screenshots vorhanden sein.**

### Verify-Screenshots → `assets/verify/1040/`
| Datei | Inhalt (eindeutiger Screen-Header) |
|-------|-------------------------------------|
| `01_basic_information.png` | 1040 Formular-Ansicht in TaxAct |
| `02_efile_center.png` | E-File Center Popup |
| `03_file_extension.png` | Filing-Screen mit Extension-Option |
| `04_federal_extension.png` | Federal Extension Screen |
| `05_application_for_automatic_extension.png` | Form 4868 Application Screen |
| `06_personal_data.png` | Personal Data Screen |
| `07_spouse.png` | Spouse Screen |
| `08_address.png` | Address Screen |
| `09_tax_liability.png` | Tax Liability Screen |
| `10_payment_amount.png` | Payment Amount Screen |
| `11_filing.png` | Filing Screen |
| `12_acknowledgement.png` | Acknowledgement Screen |
| `13_consent_to_disclosure.png` | Consent to Disclosure Screen |
| `14_alerts.png` | Review Alerts Screen |
| `14_2_third_party_designee.png` | Third Party Designee Screen (alle 3 Felder sichtbar) |
| `15_passed_alerts.png` | Passed Alerts Screen |
| `16_submit.png` | Submit E-File Screen |
| `17_successful.png` | E-File Successful Screen |
| `18_complete.png` | Filing Complete Screen |
| `19_base.png` | Client Manager Base (Ende der Iteration) |

### Button-Screenshots → `.agents/screenshots/buttons/1040/`

**Bereits vorhanden (vom User bereitgestellt):**

| Datei | Verwendung |
|-------|------------|
| `complete_form_4868_green.png` | Stage 5: Button "Complete Form 4868" |
| `efile_green.png` | Stage 11: E-File Button (grün) |
| `agree_green.png` | Stage 13: Agree/Consent Button |
| `start_alerts_green.png` | Stages 14+15: Start Alerts Button |

**Werden aus `assets/verify/1040/` kopiert (Task 0):**

`element_visible` Conditions und Click-Targets resolven gegen `screenshot_base_path` (= `.agents/screenshots/buttons/`), nicht gegen `verify_base_path`. Daher müssen die folgenden Verify-Screenshots in den Buttons-Ordner kopiert werden:

| Quelle (`assets/verify/1040/`) | Ziel (`.agents/screenshots/buttons/1040/`) | Verwendung |
|--------------------------------|--------------------------------------------|------------|
| `14_2_third_party_designee.png` | `third_party_designee.png` | Stage 15 Condition |
| `14_2_1_designee_name.png` | `label_designee_name.png` | Stage 15 Click-Target (offset_y) |
| `14_2_2_designee_phone.png` | `label_designee_phone.png` | Stage 15 Click-Target (offset_y) |
| `14_2_3_designee_PIN.png` | `label_designee_pin.png` | Stage 15 Click-Target (offset_y) |
| `17_successful.png` | `successful.png` | Stage 18 Condition |

**Aus `common/` verwendet (bereits vorhanden):**

| Datei | Verwendung |
|-------|------------|
| `common/passed_alerts.png` | Stage 16 Condition |

> **Hinweis zu Label-Screenshots:** Die kopierten Label-Crops zeigen den Beschriftungs-Text direkt oberhalb des jeweiligen Textfeldes. Der Bot klickt `offset_y=25px` unterhalb des Labels, um in das Feld zu landen. Dieser Wert kann nach erstem Test in der JSON angepasst werden.

## Research Summary

### Relevant Files
| File | Purpose | Relevante Zeilen |
|------|---------|-------|
| `config/processes/1120S.json` | Referenz-Muster für Stage-Struktur | alle |
| `clickbot/process_executor.py` | `_action_multi`, `_execute_branch`, `_action_click` (offset) | 242–263, 405–469, 657–677 |
| `clickbot/bot_controller.py` | scroll_to_top Block | ~194–205 |
| `config/settings.json` | `loop.scroll_to_top` Config | ~69–74 |

### Patterns to Follow
- **Stages 1–13**: Einfache click-Stages mit verify_screen/verify_next — exakt wie `1120S.json:1–13`
- **Konditional mit multi in if_true**: `_execute_branch` (process_executor.py:424) + `_action_multi` (657) — if_true als dict mit `"action": "multi"` ist unterstützt
- **Click mit Offset**: `_action_click` (process_executor.py:248–262) liest `offset_x`/`offset_y` aus target → für Klick unterhalb eines Labels
- **no_retry + verify_timeout**: Wie `1120S.json:stage 16` (submit_efile)
- **Conditional safeguard**: Wie `1120S.json:stage 15` (good_to_go check)

## Dependencies

- **New Packages**: keine
- **Affected Modules**: `config/processes/1040.json` (neu), `clickbot/bot_controller.py`, `config/settings.json`
- **Breaking Changes**: nein

## Tasks

### Task 0: COPY Verify-Screenshots → Buttons-Ordner

- **Action**: COPY (Dateien kopieren)
- **Implement**: 5 Verify-Screenshots nach `.agents/screenshots/buttons/1040/` kopieren, da `element_visible` Conditions und Click-Targets gegen `screenshot_base_path` (Buttons) resolven, nicht gegen `verify_base_path`.
  ```
  assets/verify/1040/14_2_third_party_designee.png → .agents/screenshots/buttons/1040/third_party_designee.png
  assets/verify/1040/14_2_1_designee_name.png      → .agents/screenshots/buttons/1040/label_designee_name.png
  assets/verify/1040/14_2_2_designee_phone.png     → .agents/screenshots/buttons/1040/label_designee_phone.png
  assets/verify/1040/14_2_3_designee_PIN.png       → .agents/screenshots/buttons/1040/label_designee_pin.png
  assets/verify/1040/17_successful.png             → .agents/screenshots/buttons/1040/successful.png
  ```
- **Depends on**: none
- **Validate**: `ls .agents/screenshots/buttons/1040/` — sollte 9 Dateien zeigen (4 bestehende + 5 kopierte)

### Task 1: CREATE `config/processes/1040.json`

- **Action**: CREATE
- **Implement**: 19-Stage Prozess-Definition. Exakte Struktur:

  | Stage | verify_screen | Action | verify_next |
  |-------|--------------|--------|-------------|
  | 1 | `1040/01_basic_information.png` | click `common/efile_menu.png` | `1040/02_efile_center.png` |
  | 2 | `1040/02_efile_center.png` | click `common/submit_electronic_filing.png` | `1040/03_file_extension.png` |
  | 3 | `1040/03_file_extension.png` | multi: click `common/file_extension_option_unchecked.png` (wait 0.5) + click `common/continue_blue.png` | `1040/04_federal_extension.png` |
  | 4 | `1040/04_federal_extension.png` | click `common/yes_green.png` | `1040/05_application_for_automatic_extension.png` |
  | 5 | `1040/05_application_for_automatic_extension.png` | click `1040/complete_form_4868_green.png` | `1040/06_personal_data.png` |
  | 6 | `1040/06_personal_data.png` | click `common/continue_blue.png` | `1040/07_spouse.png` |
  | 7 | `1040/07_spouse.png` | click `common/continue_blue.png` | `1040/08_address.png` |
  | 8 | `1040/08_address.png` | click `common/continue_blue.png` | `1040/09_tax_liability.png` |
  | 9 | `1040/09_tax_liability.png` | click `common/continue_blue.png` | `1040/10_payment_amount.png` |
  | 10 | `1040/10_payment_amount.png` | click `common/continue_blue.png` | `1040/11_filing.png` |
  | 11 | `1040/11_filing.png` | click `1040/efile_green.png` | `1040/12_acknowledgement.png` |
  | 12 | `1040/12_acknowledgement.png` | click `common/continue_blue.png` | `1040/13_consent_to_disclosure.png` |
  | 13 | `1040/13_consent_to_disclosure.png` | click `1040/agree_green.png` | `1040/14_alerts.png` |
  | 14 | `1040/14_alerts.png` | click `1040/start_alerts_green.png` | — (wait_after: 2.0) |
  | 15 | — | conditional: element_visible `1040/third_party_designee.png` (buttons) → if_true: multi[click+type name, click+type phone, click+type PIN, continue, start_alerts] / if_false: continue | — |
  | 16 | — | conditional: element_visible `common/passed_alerts.png` (buttons) → if_true: click `common/continue_blue.png` (verify_next: `1040/16_submit.png`) / if_false: click `common/clients_button.png` | — |
  | 17 | `1040/16_submit.png` | click `common/submit_efile.png`, no_retry: true, verify_timeout: 30.0 | `1040/17_successful.png` |
  | 18 | — | conditional: element_visible `1040/successful.png` (buttons) → if_true: click `common/continue_blue.png` (verify_next: `1040/18_complete.png`) / if_false: click `common/clients_button.png` | — |
  | 19 | `1040/18_complete.png` | click `common/clients_button.png` | `1040/19_base.png` |

  **Stage 15 if_true multi-Actions (Designee Sub-Flow):**
  ```
  1. click target=1040/label_designee_name.png, offset_y=25, wait_after=0.3
  2. type text_value="TATIANA MOROZ", clear_first=true, wait_after=0.5
  3. click target=1040/label_designee_phone.png, offset_y=25, wait_after=0.3
  4. type text_value="(847)850-0085", clear_first=true, wait_after=0.5
  5. click target=1040/label_designee_pin.png, offset_y=25, wait_after=0.3
  6. type text_value="12345", clear_first=true, wait_after=0.5
  7. click target=common/continue_blue.png, wait_after=2.0
  8. click target=1040/start_alerts_green.png, wait_after=2.0
  ```

  **static_inputs:** `{}` (Designee-Daten sind hardcoded in stage 15 als text_value)

- **Pattern**: `config/processes/1120S.json` für Gesamtstruktur; stage 4 für multi; stage 15 für conditional safeguard
- **Depends on**: Task 0 (Button-Screenshots müssen kopiert sein)
- **Validate**: `python -c "from clickbot.process_loader import load_process; p=load_process('1040'); print(len(p['stages']), 'stages')"`

### Task 2: UPDATE `clickbot/bot_controller.py` — Ctrl+Home statt scroll

- **Action**: UPDATE
- **Implement**:
  1. `import pyautogui` am Anfang der Datei hinzufügen (nach den bestehenden Imports)
  2. Den scroll_to_top Block (~Zeile 194–205) ersetzen:
     ```python
     # Scroll client list to top via Ctrl+Home (instant, reliable regardless of list size)
     scroll_top = self.settings.get("loop", {}).get("scroll_to_top", {})
     if scroll_top.get("enabled", True):
         pyautogui.hotkey('ctrl', 'home')
         time.sleep(scroll_top.get("delay_s", 0.3))
     ```
- **Pattern**: `bot_controller.py:194` (bestehender scroll_to_top Block)
- **Depends on**: none
- **Validate**: `python -c "from clickbot.bot_controller import BotController; print('OK')"`

### Task 3: UPDATE `config/settings.json` — scroll_to_top vereinfachen

- **Action**: UPDATE
- **Implement**: `loop.scroll_to_top` auf das neue Schema umstellen:
  ```json
  "scroll_to_top": {
    "enabled": true,
    "delay_s": 0.3
  }
  ```
  `x`, `y`, `amount` Felder entfernen (nicht mehr benötigt)
- **Pattern**: `config/settings.json:69–74`
- **Depends on**: Task 2
- **Validate**: `python -c "import json; s=json.load(open('config/settings.json')); print(s['loop']['scroll_to_top'])"`

### Task 4: RUN Testsuite

- **Action**: keine Code-Änderung
- **Implement**: Testsuite ausführen, alle Fehler beheben
- **Depends on**: Tasks 0–3
- **Validate**: `pytest tests/unit -v`

## Testing Requirements

- [ ] `load_process('1040')` lädt ohne Fehler, gibt 19 Stages zurück
- [ ] `load_process('1120S')` und `load_process('1120')` weiterhin unverändert ladevbar
- [ ] `BotController` importiert pyautogui ohne Fehler
- [ ] Edge case: `scroll_to_top.enabled: false` in settings → kein Ctrl+Home

**Test Levels**: Unit (Task 1 Validierung), Manuell (E2E gegen TaxAct)

## Bug Handling

- Bugs durch diese Änderungen → sofort fixen
- Pre-existing Bugs → `.agents/bugs/` dokumentieren, NICHT fixen
- NIEMALS Code außerhalb des Scopes ändern

## Rollback Strategy

1. `git checkout -- clickbot/bot_controller.py config/settings.json`
2. `rm config/processes/1040.json`
3. `pytest tests/unit -v`

## Manual Verification

- [ ] 1040-Client wird in der GUI mit Return-Type "1040" ausgewählt
- [ ] Bot durchläuft alle 19 Stages ohne Fehler (ohne Third-Party Designee)
- [ ] Bot durchläuft alle 19 Stages inkl. Designee-Sub-Flow korrekt
- [ ] Nach Iteration: Ctrl+Home springt sofort zum Anfang der Client-Liste
- [ ] 1120S- und 1120-Clients weiterhin unverändert funktionsfähig

## Notes

- **offset_y für Designee-Felder**: Startwert `25` — nach erstem Test ggf. in `1040.json` auf den tatsächlichen Abstand Label→Textfeld anpassen
- **Pfadauflösung**: `element_visible` Conditions und Click-Targets resolven gegen `screenshot_base_path` (`.agents/screenshots/buttons/`), `verify_screen`/`verify_next` gegen `verify_base_path` (`assets/verify/`). Deshalb kopiert Task 0 die benötigten Verify-Screenshots in den Buttons-Ordner.
- **Ctrl+Home funktioniert nur wenn Client-Liste nicht fokussiert ist**: Nach stage 19 (clients_button click → base) ist die Liste nicht fokussiert → timing passt. Falls Problem auftritt, `delay_s` erhöhen
- **`normalize_return_type` kein Blocker**: Da Phase 9 (GUI Return-Type Selection) bereits implementiert ist, wird `normalize_return_type` im Hauptflow nicht mehr aufgerufen. Der Return-Type kommt direkt aus der GUI-Auswahl.
