# Feature: Phase 4 - Mock-up Modus mit TaxAct Simulator GUI

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

## Feature Description

Implementierung eines **TaxAct Simulator** - einer eigenständigen GUI-Anwendung, die TaxAct 2025 nachbildet. Diese Mock-GUI zeigt exakt die gleichen Screens, Buttons und Textfelder wie der echte 1120/1120S E-File Extension Prozess.

**Kern-Konzept:**
- **Fullscreen-Fenster** mit Titel "TaxAct 2025 Professional - [Simulator]"
- **Screen-by-Screen Navigation** entsprechend der Process JSONs
- **Pixel-genaue Button-Positionen** wie in den existierenden Screenshots
- **Interaktive Elemente** die auf Klicks reagieren und zum nächsten Screen wechseln
- **Textfelder** die ausgefüllt werden können
- **Checkboxen** mit korrektem Zustand
- **Client Manager Tabelle** mit Mock-Daten (verschiedene Return Types, Fed EF Status)

Der Bot kann dann gegen diese Mock-GUI laufen und seine gesamte Logik testen, ohne echtes TaxAct zu benötigen.

## User Story

As a **Entwickler** I want to **den Bot gegen eine TaxAct-Simulation testen** so that **ich die Automatisierung entwickeln und debuggen kann, ohne Zugang zu echtem TaxAct oder Remote Desktop zu benötigen**.

## Problem Statement

- Phase 3 ist implementiert, aber E2E-Testing scheitert wegen RDP-Screenshot-Problemen
- Ohne Test-Umgebung kann keine weitere Entwicklung stattfinden
- 1120S-Prozess kann nicht entwickelt werden ohne Test-Möglichkeit

## Solution Statement

Erstelle eine **TaxAct Simulator GUI** (`taxact_simulator.py`) die:
1. Als separates Fenster läuft (Fullscreen 1920x1080)
2. Die existierenden Button-Screenshots als UI-Elemente verwendet
3. Auf Klicks reagiert und Screens wechselt
4. Den Bot "täuscht" - Template Matching findet die echten Button-Bilder

## Feature Metadata

**Feature Type**: New Capability (Development/Testing Infrastructure)
**Estimated Complexity**: High
**Primary Systems Affected**: Neues Modul `taxact_simulator.py`, Integration mit Test-Suite
**Dependencies**: CustomTkinter (bereits vorhanden), PIL/Pillow (bereits vorhanden)

---

## CONTEXT REFERENCES

### Relevant Codebase Files (MUST READ BEFORE IMPLEMENTING!)

| File | Lines | Why |
|------|-------|-----|
| `config/processes/1120.json` | Full | Definiert alle 36 Screens und deren Elemente |
| `.agents/screenshots/buttons/common/` | Directory | Existierende Button-Screenshots als UI-Elemente |
| `.agents/screenshots/buttons/1120/` | Directory | 1120-spezifische Screenshots |
| `clickbot/gui.py` | Full | CustomTkinter Pattern für GUI-Entwicklung |
| `clickbot/vision.py` | 120-191 | Template Matching - so "sieht" der Bot die Buttons |
| `config/settings.json` | 49-59 | client_table Settings für Mock-Daten |

### New Files to Create

| File | Purpose |
|------|---------|
| `simulator/taxact_simulator.py` | Hauptmodul für TaxAct Mock-GUI |
| `simulator/screens.py` | Screen-Definitionen (welche Elemente wo) |
| `simulator/mock_data.py` | Mock Client-Daten für Client Manager |
| `simulator/__init__.py` | Package-Init |
| `config/simulator_settings.json` | Simulator-Konfiguration |

### Files to Modify

| File | Changes |
|------|---------|
| `config/settings.json` | `mock_mode` Flag hinzufügen |
| `CLAUDE.md` | Simulator-Dokumentation hinzufügen |

### Relevant Documentation

| Source | Section | Why |
|--------|---------|-----|
| [CustomTkinter Docs](https://customtkinter.tomschimansky.com/) | CTkImage, CTkButton | Für Button-Rendering mit Bildern |
| [Pillow Docs](https://pillow.readthedocs.io/) | Image.open | Laden der Screenshot-Bilder |

### Patterns to Follow

**GUI Pattern (aus gui.py):**
```python
class SimulatorWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TaxAct 2025 Professional - [Simulator]")
        self.geometry("1920x1080")
        self.resizable(False, False)

        self.current_screen = "client_manager"
        self._setup_screen()
```

**Screen Navigation Pattern:**
```python
def _on_button_click(self, next_screen: str) -> None:
    """Handle button click and navigate to next screen."""
    logger.info(f"Button clicked, navigating to: {next_screen}")
    self.current_screen = next_screen
    self._clear_screen()
    self._setup_screen()
```

---

## ARCHITEKTUR-KONZEPT

### Screen-basierte Navigation

```
┌─────────────────────────────────────────────────────────────────┐
│                    TaxAct Simulator GUI                          │
│                     (1920x1080 Fullscreen)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Screen: client_manager                                   │   │
│  │                                                           │   │
│  │  [E-File Menu Button @ 850,45]                           │   │
│  │                                                           │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ Client Name    │ Return Type │ Fed EF Status       │ │   │
│  │  ├────────────────┼─────────────┼─────────────────────┤ │   │
│  │  │ SANDMEYER INC  │ 1120        │ [empty]             │ │   │
│  │  │ SMITH LLC      │ 1120S       │ [empty]             │ │   │
│  │  │ JONES CORP     │ 1120        │ Submitted           │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Current Screen: client_manager                                  │
│  Next Expected: click on client row → efile_popup               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Screen-Definition Format

```python
SCREENS = {
    "client_manager": {
        "background": "screens/client_manager_bg.png",  # Optional
        "elements": [
            {
                "type": "button",
                "image": "common/efile_menu.png",
                "position": (850, 45),  # Exakte Position wie in TaxAct
                "on_click": "efile_popup"
            },
            {
                "type": "table",
                "id": "client_table",
                "position": (50, 145),
                "data_source": "mock_clients"
            }
        ]
    },
    "efile_popup": {
        "elements": [
            {
                "type": "button",
                "image": "common/submit_electronic_filing.png",
                "position": (500, 300),
                "on_click": "filing_screen"
            }
        ]
    },
    # ... weitere Screens
}
```

### Wie der Bot die Simulator-GUI "sieht"

```
Bot führt aus:                     Simulator reagiert:
─────────────────                  ──────────────────
1. take_screenshot()        →      Screenshot der Simulator-GUI
2. find_element("efile.png") →     Findet Button (echtes PNG eingebettet)
3. click(850, 45)           →      on_click Event → nächster Screen
4. take_screenshot()        →      Neuer Screen mit neuen Buttons
```

---

## IMPLEMENTATION PLAN

### Phase 1: Simulator Framework

Erstelle die Basis-Struktur für den TaxAct Simulator.

**Tasks:**
- Simulator-Package erstellen
- Hauptfenster mit Fullscreen 1920x1080
- Screen-Wechsel-Logik
- Button-Rendering mit echten Screenshots

### Phase 2: Screen Definitionen

Definiere alle Screens basierend auf 1120.json Process.

**Tasks:**
- Screens aus 1120.json extrahieren
- Element-Positionen festlegen
- Navigation-Flow definieren

### Phase 3: Client Manager mit Mock-Daten

Implementiere die Client-Tabelle mit konfigurierbaren Mock-Daten.

**Tasks:**
- Mock-Daten definieren (Client Name, Return Type, Fed EF Status)
- Tabellen-Rendering
- Doppelklick auf Client öffnet Form

### Phase 4: Interaktive Elemente

Implementiere Checkboxen, Textfelder und bedingte Screens.

**Tasks:**
- Checkbox-Toggle
- Textfeld-Input
- Bedingte Navigation (Error vs Passed Alerts)

### Phase 5: 1120S Support

Erweitere Simulator um 1120S-spezifische Screens.

**Tasks:**
- 1120S Screen-Definitionen
- Unterschiedliche Navigation für 1120S
- Return-Type-basierte Screen-Auswahl

### Phase 6: Integration & Testing

Teste Bot gegen Simulator.

**Tasks:**
- Bot gegen Simulator laufen lassen
- Alle 36 Steps verifizieren
- Timing-Anpassungen

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

---

### Task 1: CREATE simulator/__init__.py

- **IMPLEMENT**: Package-Initialisierung
- **PATTERN**: Bestehende __init__.py Struktur
- **VALIDATE**: `python -c "import simulator; print('OK')"`

```python
"""TaxAct Simulator - Mock GUI for bot testing.

Provides a pixel-accurate simulation of TaxAct 2025 Professional
for testing the automation bot without real TaxAct access.
"""

__version__ = "1.0.0"
```

---

### Task 2: CREATE simulator/mock_data.py

- **IMPLEMENT**: Mock-Daten für Client Manager Tabelle
- **PATTERN**: Dataclass für strukturierte Daten
- **VALIDATE**: `python -c "from simulator.mock_data import MOCK_CLIENTS; print(len(MOCK_CLIENTS), 'clients')"`

```python
"""Mock data for TaxAct Simulator.

Provides configurable test data for the Client Manager table.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class MockClient:
    """Mock client data for testing."""
    name: str
    return_type: str  # "1120" or "1120S"
    fed_ef_status: str  # "" (empty), "Submitted", "Accepted", etc.

    @property
    def needs_processing(self) -> bool:
        """Check if client needs E-File processing."""
        return self.fed_ef_status == ""


# Default mock clients for testing
MOCK_CLIENTS: List[MockClient] = [
    MockClient("SANDMEYER INC", "1120", ""),
    MockClient("SMITH LLC", "1120S", ""),
    MockClient("JONES CORP", "1120", "Submitted"),
    MockClient("TECH SOLUTIONS", "1120S", ""),
    MockClient("ABC HOLDINGS", "1120", ""),
    MockClient("XYZ PARTNERS", "1120S", "Accepted"),
    MockClient("ACME CORP", "1120", ""),
    MockClient("BETA INDUSTRIES", "1120S", ""),
    MockClient("GAMMA LLC", "1120", "Rejected"),
    MockClient("DELTA INC", "1120", ""),
]


def get_clients_by_return_type(return_type: str) -> List[MockClient]:
    """Get all clients with specific return type."""
    return [c for c in MOCK_CLIENTS if c.return_type == return_type]


def get_unprocessed_clients() -> List[MockClient]:
    """Get all clients with empty Fed EF Status."""
    return [c for c in MOCK_CLIENTS if c.needs_processing]
```

---

### Task 3: CREATE simulator/screens.py

- **IMPLEMENT**: Screen-Definitionen für alle 36 Steps des 1120-Prozesses
- **PATTERN**: Dictionary-basierte Screen-Definition
- **VALIDATE**: `python -c "from simulator.screens import SCREENS_1120; print(len(SCREENS_1120), 'screens')"`

```python
"""Screen definitions for TaxAct Simulator.

Each screen defines:
- elements: List of UI elements (buttons, checkboxes, textfields, labels)
- Each element has: type, image (for buttons), position, and action

Positions are based on actual TaxAct 2025 at 1920x1080 resolution.
"""

from typing import Any, Dict, List

# Button image base path (relative to .agents/screenshots/buttons/)
IMG_BASE = ".agents/screenshots/buttons"


def _btn(image: str, pos: tuple, next_screen: str = None, action: str = None) -> Dict[str, Any]:
    """Helper to create button element."""
    return {
        "type": "button",
        "image": image,
        "position": pos,
        "next_screen": next_screen,
        "action": action
    }


def _checkbox(checked_img: str, unchecked_img: str, pos: tuple, default_checked: bool = False) -> Dict[str, Any]:
    """Helper to create checkbox element."""
    return {
        "type": "checkbox",
        "image_checked": checked_img,
        "image_unchecked": unchecked_img,
        "position": pos,
        "checked": default_checked
    }


def _textfield(label_img: str, label_pos: tuple, field_offset: tuple = (150, 0),
               field_size: tuple = (200, 25), field_id: str = None) -> Dict[str, Any]:
    """Helper to create textfield element."""
    return {
        "type": "textfield",
        "label_image": label_img,
        "label_position": label_pos,
        "field_offset": field_offset,
        "field_size": field_size,
        "field_id": field_id,
        "value": ""
    }


def _label(text: str, pos: tuple, font_size: int = 14) -> Dict[str, Any]:
    """Helper to create text label."""
    return {
        "type": "label",
        "text": text,
        "position": pos,
        "font_size": font_size
    }


# =============================================================================
# FORM 1120 SCREENS (36 Steps)
# =============================================================================

SCREENS_1120: Dict[str, Dict[str, Any]] = {

    # -------------------------------------------------------------------------
    # Screen 0: Client Manager (Base/Start)
    # -------------------------------------------------------------------------
    "client_manager": {
        "title": "Client Manager",
        "elements": [
            _btn("common/efile_menu.png", (850, 45), next_screen="efile_popup"),
            _btn("common/clients_button.png", (50, 45)),  # Already on this screen
            {
                "type": "client_table",
                "position": (50, 145),
                "row_height": 25,
                "columns": ["Client Name", "Return Type", "Fed EF Status"],
                "column_widths": [250, 80, 100]
            }
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 1: E-File Popup (after clicking E-File menu)
    # -------------------------------------------------------------------------
    "efile_popup": {
        "title": "E-File Center",
        "is_popup": True,
        "elements": [
            _label("E-File Center", (400, 100), font_size=18),
            _btn("common/submit_electronic_filing.png", (400, 250), next_screen="filing_screen"),
            _btn("common/popup_close_x.png", (750, 80), next_screen="client_manager"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 2: Filing Screen (File Extension selection)
    # -------------------------------------------------------------------------
    "filing_screen": {
        "title": "Filing",
        "elements": [
            _label("What would you like to do?", (400, 150), font_size=16),
            _btn("common/file_extension_option_unchecked.png", (400, 250), action="select_extension"),
            _btn("common/continue_blue.png", (850, 650), next_screen="federal_extension"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 3: Federal Extension (Yes/No)
    # -------------------------------------------------------------------------
    "federal_extension": {
        "title": "Federal Extension",
        "elements": [
            _label("Would you like to file a Federal Extension?", (400, 200), font_size=16),
            _btn("common/yes_green.png", (400, 350), next_screen="form_7004_intro"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 4: Form 7004 Intro
    # -------------------------------------------------------------------------
    "form_7004_intro": {
        "title": "Form 7004 - Application for Extension",
        "elements": [
            _label("Form 7004 - Application for Automatic Extension", (400, 150), font_size=18),
            _btn("1120/complete_form_7004.png", (400, 350), next_screen="corporation_name"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 5: Corporation Name
    # -------------------------------------------------------------------------
    "corporation_name": {
        "title": "Corporation Name",
        "elements": [
            _label("Corporation Name", (400, 150), font_size=16),
            _label("SANDMEYER INC", (400, 250), font_size=14),  # From mock data
            _btn("common/continue_blue.png", (850, 650), next_screen="homeowners_assoc"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 6: Homeowners Association Checkbox
    # -------------------------------------------------------------------------
    "homeowners_assoc": {
        "title": "Homeowners Association",
        "elements": [
            _label("Is this a Homeowners Association?", (400, 200), font_size=16),
            _checkbox(
                "1120/checkbox_homeowners_checked.png",
                "1120/checkbox_homeowners_unchecked.png",
                (400, 300),
                default_checked=False
            ),
            _btn("common/continue_blue.png", (850, 650), next_screen="address"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 7: Address
    # -------------------------------------------------------------------------
    "address": {
        "title": "Address",
        "elements": [
            _label("Business Address", (400, 150), font_size=16),
            _label("123 Main Street, Chicago, IL 60601", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="federal_id"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 8: Federal ID Number
    # -------------------------------------------------------------------------
    "federal_id": {
        "title": "Federal ID Number",
        "elements": [
            _label("Employer Identification Number (EIN)", (400, 150), font_size=16),
            _label("12-3456789", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="fiscal_year"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 9: Fiscal Year
    # -------------------------------------------------------------------------
    "fiscal_year": {
        "title": "Fiscal Year",
        "elements": [
            _label("Tax Year", (400, 150), font_size=16),
            _label("Calendar Year 2025", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="todays_date"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 10: Today's Date
    # -------------------------------------------------------------------------
    "todays_date": {
        "title": "Today's Date",
        "elements": [
            _label("Today's Date", (400, 150), font_size=16),
            _label("02/10/2026", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="no_office_us"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 11: No Office in US Checkbox
    # -------------------------------------------------------------------------
    "no_office_us": {
        "title": "No Office in United States",
        "elements": [
            _label("No office or place of business in the United States?", (400, 200), font_size=16),
            _checkbox(
                "1120/checkbox_no_office_checked.png",
                "1120/checkbox_no_office_unchecked.png",
                (400, 300),
                default_checked=False
            ),
            _btn("common/continue_blue.png", (850, 650), next_screen="section_checkbox"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 12: Section 1.6081-5 Checkbox
    # -------------------------------------------------------------------------
    "section_checkbox": {
        "title": "Section 1.6081-5",
        "elements": [
            _label("Section 1.6081-5 Election?", (400, 200), font_size=16),
            _checkbox(
                "1120/checkbox_section_checked.png",
                "1120/checkbox_section_unchecked.png",
                (400, 300),
                default_checked=False
            ),
            _btn("common/continue_blue.png", (850, 650), next_screen="tax_liability"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 13: Tax Liability (Scrollable)
    # -------------------------------------------------------------------------
    "tax_liability": {
        "title": "Tax Liability and Payments",
        "scrollable": True,
        "scroll_to_reveal": "common/continue_blue.png",
        "elements": [
            _label("Tax Liability and Payments", (400, 150), font_size=16),
            _label("Estimated tax liability: $0", (400, 300), font_size=14),
            _label("Total payments: $0", (400, 350), font_size=14),
            _label("Balance due: $0", (400, 400), font_size=14),
            # Continue button is below the fold - requires scroll
            _btn("common/continue_blue.png", (850, 850), next_screen="payment_amount"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 14: Payment Amount
    # -------------------------------------------------------------------------
    "payment_amount": {
        "title": "Payment Amount",
        "elements": [
            _label("Payment Amount", (400, 150), font_size=16),
            _label("Amount to pay with extension: $0.00", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="print_form_7004"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 15: Print Form 7004
    # -------------------------------------------------------------------------
    "print_form_7004": {
        "title": "Print Form 7004",
        "elements": [
            _label("Form 7004 Ready", (400, 150), font_size=16),
            _btn("1120/efile_form_7004.png", (400, 350), next_screen="acknowledgment"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 16: Acknowledgment Status
    # -------------------------------------------------------------------------
    "acknowledgment": {
        "title": "Acknowledgment Status",
        "elements": [
            _label("Acknowledgment Status", (400, 150), font_size=16),
            _label("Pending submission...", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="signing_officer_info"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 17: Signing Officer Information (Textfields)
    # -------------------------------------------------------------------------
    "signing_officer_info": {
        "title": "Signing Officer Information",
        "elements": [
            _label("Signing Officer Information", (400, 100), font_size=18),
            _textfield("1120/label_title.png", (200, 200), field_id="officer_title"),
            _textfield("1120/label_email.png", (200, 260), field_offset=(150, 0),
                      field_size=(250, 25), field_id="officer_email"),
            _textfield("1120/label_phone.png", (200, 320), field_offset=(150, 0),
                      field_size=(150, 25), field_id="officer_phone"),
            _btn("common/continue_blue.png", (850, 650), next_screen="officer_signature"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 18: Officer's Signature (PIN Entry)
    # -------------------------------------------------------------------------
    "officer_signature": {
        "title": "Officer's Signature",
        "elements": [
            _label("Officer's Signature", (400, 100), font_size=18),
            _textfield("1120/label_pin.png", (200, 250), field_offset=(150, 0),
                      field_size=(100, 25), field_id="officer_pin"),
            _btn("common/continue_blue.png", (850, 650), next_screen="ero_signature"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 19: ERO Signature
    # -------------------------------------------------------------------------
    "ero_signature": {
        "title": "ERO Signature",
        "elements": [
            _label("ERO Signature", (400, 150), font_size=16),
            _label("Electronic Return Originator signature on file.", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="federal_efile_alerts"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 20: Federal E-File Alerts
    # -------------------------------------------------------------------------
    "federal_efile_alerts": {
        "title": "Federal E-File Alerts",
        "elements": [
            _label("Federal E-File Alerts", (400, 150), font_size=16),
            _label("Run alerts to check for errors before submission.", (400, 250), font_size=14),
            _btn("1120/start_form_7004_alerts.png", (400, 400), next_screen="alerts_result"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 21a: Alerts Result - PASSED (Conditional)
    # -------------------------------------------------------------------------
    "alerts_result": {
        "title": "Alerts Result",
        "conditional": True,
        "condition_var": "alerts_passed",  # True = passed, False = error
        "elements_if_true": [
            _label("Alerts Result", (400, 150), font_size=16),
            {
                "type": "image",
                "image": "common/passed_alerts.png",
                "position": (400, 300)
            },
            _btn("common/continue_blue.png", (850, 650), next_screen="submit_efile"),
        ],
        "elements_if_false": [
            _label("Alerts Result - Errors Found", (400, 150), font_size=16),
            _label("Error: Missing information", (400, 300), font_size=14),
            _btn("common/clients_button.png", (50, 45), next_screen="client_manager"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 22: Submit E-File
    # -------------------------------------------------------------------------
    "submit_efile": {
        "title": "Submit E-File",
        "elements": [
            _label("Ready to Submit", (400, 150), font_size=16),
            _label("Click Submit to file your extension.", (400, 250), font_size=14),
            _btn("1120/submit_efile.png", (400, 400), next_screen="confirmation"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 23: Confirmation (Green Continue)
    # -------------------------------------------------------------------------
    "confirmation": {
        "title": "Confirmation",
        "elements": [
            _label("Extension Submitted Successfully!", (400, 200), font_size=18),
            _label("Your Form 7004 has been submitted.", (400, 300), font_size=14),
            _btn("common/continue_green.png", (850, 650), next_screen="filing_complete"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 24: Filing Complete
    # -------------------------------------------------------------------------
    "filing_complete": {
        "title": "Filing Complete",
        "elements": [
            _label("Filing Complete", (400, 150), font_size=18),
            _label("What would you like to do next?", (400, 250), font_size=14),
            _btn("common/new_return.png", (400, 400), next_screen="add_client_popup"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 25: Add Client Popup
    # -------------------------------------------------------------------------
    "add_client_popup": {
        "title": "Add Client",
        "is_popup": True,
        "elements": [
            _label("Add New Client", (400, 150), font_size=16),
            _btn("common/popup_close_x.png", (750, 100), next_screen="client_manager"),
        ]
    },
}


# =============================================================================
# FORM 1120S SCREENS (Placeholder - to be filled)
# =============================================================================

SCREENS_1120S: Dict[str, Dict[str, Any]] = {
    # 1120S has different screens - will be defined based on actual process
    "client_manager": SCREENS_1120["client_manager"],  # Same as 1120
    # ... additional 1120S-specific screens
}


def get_screens(return_type: str) -> Dict[str, Dict[str, Any]]:
    """Get screen definitions for return type."""
    if return_type == "1120":
        return SCREENS_1120
    elif return_type == "1120S":
        return SCREENS_1120S
    else:
        raise ValueError(f"Unknown return type: {return_type}")
```

---

### Task 4: CREATE simulator/taxact_simulator.py

- **IMPLEMENT**: Haupt-Simulator GUI mit Screen-Rendering und Navigation
- **PATTERN**: CustomTkinter wie in gui.py
- **VALIDATE**: `python -m simulator.taxact_simulator`

```python
"""TaxAct Simulator - Mock GUI for testing the automation bot.

This application simulates TaxAct 2025 Professional at 1920x1080 resolution.
It uses the same button screenshots that the bot looks for, so the bot's
template matching will find the correct elements.

Usage:
    python -m simulator.taxact_simulator

The simulator will open fullscreen and display the Client Manager.
Click through screens or let the bot automate through them.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import customtkinter as ctk
from PIL import Image, ImageTk

from simulator.screens import SCREENS_1120, SCREENS_1120S, get_screens
from simulator.mock_data import MOCK_CLIENTS, MockClient

logger = logging.getLogger(__name__)

# Configure appearance
ctk.set_appearance_mode("light")  # TaxAct uses light theme


class TaxActSimulator(ctk.CTk):
    """TaxAct 2025 Professional Simulator.

    Provides a pixel-accurate simulation of TaxAct for testing
    the automation bot without real TaxAct access.
    """

    def __init__(self):
        super().__init__()

        # Window setup - match TaxAct exactly
        self.title("TaxAct 2025 Professional - [Simulator]")
        self.geometry("1920x1080")
        self.resizable(False, False)

        # State
        self.current_screen = "client_manager"
        self.current_return_type = "1120"
        self.screens = get_screens(self.current_return_type)
        self.selected_client: Optional[MockClient] = None
        self.textfield_values: Dict[str, str] = {}
        self.checkbox_states: Dict[str, bool] = {}
        self.alerts_passed = True  # Can be toggled for testing

        # Image cache
        self._image_cache: Dict[str, ctk.CTkImage] = {}

        # Screenshot base path
        self.img_base = Path(".agents/screenshots/buttons")

        # Setup
        self._setup_ui()
        self._render_screen()

        logger.info("TaxAct Simulator initialized")

    def _setup_ui(self):
        """Setup base UI structure."""
        # Main frame fills entire window
        self.main_frame = ctk.CTkFrame(self, fg_color="#f0f0f0", corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)

        # Status bar at bottom
        self.status_frame = ctk.CTkFrame(self, height=30, fg_color="#e0e0e0")
        self.status_frame.pack(side="bottom", fill="x")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text=f"Screen: {self.current_screen} | Return Type: {self.current_return_type}",
            font=("Consolas", 12)
        )
        self.status_label.pack(side="left", padx=10)

        # Debug toggle
        self.debug_var = ctk.BooleanVar(value=True)
        self.debug_check = ctk.CTkCheckBox(
            self.status_frame,
            text="Show Debug Info",
            variable=self.debug_var,
            command=self._render_screen
        )
        self.debug_check.pack(side="right", padx=10)

        # Alerts toggle (for testing error path)
        self.alerts_var = ctk.BooleanVar(value=True)
        self.alerts_check = ctk.CTkCheckBox(
            self.status_frame,
            text="Alerts Pass",
            variable=self.alerts_var,
            command=self._on_alerts_toggle
        )
        self.alerts_check.pack(side="right", padx=10)

    def _on_alerts_toggle(self):
        """Handle alerts pass/fail toggle."""
        self.alerts_passed = self.alerts_var.get()
        if self.current_screen == "alerts_result":
            self._render_screen()

    def _clear_screen(self):
        """Clear all widgets from main frame."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def _load_image(self, image_path: str, size: tuple = None) -> Optional[ctk.CTkImage]:
        """Load image from path, with caching."""
        cache_key = f"{image_path}_{size}"

        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        full_path = self.img_base / image_path

        if not full_path.exists():
            logger.warning(f"Image not found: {full_path}")
            return None

        try:
            pil_image = Image.open(full_path)

            if size:
                pil_image = pil_image.resize(size, Image.Resampling.LANCZOS)

            ctk_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=pil_image.size
            )

            self._image_cache[cache_key] = ctk_image
            return ctk_image

        except Exception as e:
            logger.error(f"Failed to load image {full_path}: {e}")
            return None

    def _render_screen(self):
        """Render the current screen."""
        self._clear_screen()

        screen_def = self.screens.get(self.current_screen)
        if not screen_def:
            logger.error(f"Unknown screen: {self.current_screen}")
            return

        # Handle conditional screens
        if screen_def.get("conditional"):
            condition_var = screen_def.get("condition_var")
            if condition_var == "alerts_passed":
                elements = screen_def.get("elements_if_true" if self.alerts_passed else "elements_if_false", [])
            else:
                elements = screen_def.get("elements", [])
        else:
            elements = screen_def.get("elements", [])

        # Update status
        title = screen_def.get("title", self.current_screen)
        self.status_label.configure(
            text=f"Screen: {title} | Return Type: {self.current_return_type} | "
                 f"Client: {self.selected_client.name if self.selected_client else 'None'}"
        )

        # Render title
        if "title" in screen_def:
            title_label = ctk.CTkLabel(
                self.main_frame,
                text=screen_def["title"],
                font=("Segoe UI", 24, "bold"),
                text_color="#333333"
            )
            title_label.place(x=50, y=20)

        # Render elements
        for element in elements:
            self._render_element(element)

        # Show debug info
        if self.debug_var.get():
            self._render_debug_info(elements)

    def _render_element(self, element: Dict[str, Any]):
        """Render a single UI element."""
        elem_type = element.get("type")
        pos = element.get("position", (0, 0))

        if elem_type == "button":
            self._render_button(element, pos)
        elif elem_type == "checkbox":
            self._render_checkbox(element, pos)
        elif elem_type == "textfield":
            self._render_textfield(element)
        elif elem_type == "label":
            self._render_label(element, pos)
        elif elem_type == "image":
            self._render_image(element, pos)
        elif elem_type == "client_table":
            self._render_client_table(element, pos)

    def _render_button(self, element: Dict[str, Any], pos: tuple):
        """Render a button with image."""
        image_path = element.get("image")
        next_screen = element.get("next_screen")
        action = element.get("action")

        image = self._load_image(image_path)

        if image:
            btn = ctk.CTkButton(
                self.main_frame,
                image=image,
                text="",
                fg_color="transparent",
                hover_color="#e0e0e0",
                corner_radius=0,
                command=lambda: self._on_button_click(next_screen, action)
            )
            # Place at center of position
            btn.place(x=pos[0] - image._size[0]//2, y=pos[1] - image._size[1]//2)
        else:
            # Fallback text button
            btn = ctk.CTkButton(
                self.main_frame,
                text=f"[{image_path}]",
                command=lambda: self._on_button_click(next_screen, action)
            )
            btn.place(x=pos[0], y=pos[1])

    def _render_checkbox(self, element: Dict[str, Any], pos: tuple):
        """Render a checkbox with checked/unchecked images."""
        checked_img = element.get("image_checked")
        unchecked_img = element.get("image_unchecked")
        default_checked = element.get("checked", False)

        # Get or set state
        checkbox_id = f"{self.current_screen}_{pos}"
        if checkbox_id not in self.checkbox_states:
            self.checkbox_states[checkbox_id] = default_checked

        is_checked = self.checkbox_states[checkbox_id]
        image_path = checked_img if is_checked else unchecked_img
        image = self._load_image(image_path)

        if image:
            btn = ctk.CTkButton(
                self.main_frame,
                image=image,
                text="",
                fg_color="transparent",
                hover_color="#e0e0e0",
                corner_radius=0,
                command=lambda: self._toggle_checkbox(checkbox_id)
            )
            btn.place(x=pos[0] - image._size[0]//2, y=pos[1] - image._size[1]//2)

    def _toggle_checkbox(self, checkbox_id: str):
        """Toggle checkbox state and re-render."""
        self.checkbox_states[checkbox_id] = not self.checkbox_states.get(checkbox_id, False)
        self._render_screen()

    def _render_textfield(self, element: Dict[str, Any]):
        """Render a label + textfield combination."""
        label_img = element.get("label_image")
        label_pos = element.get("label_position", (0, 0))
        field_offset = element.get("field_offset", (150, 0))
        field_size = element.get("field_size", (200, 25))
        field_id = element.get("field_id", "unknown")

        # Render label image
        image = self._load_image(label_img)
        if image:
            label = ctk.CTkLabel(self.main_frame, image=image, text="")
            label.place(x=label_pos[0], y=label_pos[1])

        # Render textfield
        field_x = label_pos[0] + field_offset[0]
        field_y = label_pos[1] + field_offset[1]

        entry = ctk.CTkEntry(
            self.main_frame,
            width=field_size[0],
            height=field_size[1],
            font=("Segoe UI", 12)
        )
        entry.place(x=field_x, y=field_y)

        # Restore value if exists
        if field_id in self.textfield_values:
            entry.insert(0, self.textfield_values[field_id])

        # Save on change
        entry.bind("<KeyRelease>", lambda e: self._on_textfield_change(field_id, entry.get()))

    def _on_textfield_change(self, field_id: str, value: str):
        """Handle textfield value change."""
        self.textfield_values[field_id] = value

    def _render_label(self, element: Dict[str, Any], pos: tuple):
        """Render a text label."""
        text = element.get("text", "")
        font_size = element.get("font_size", 14)

        label = ctk.CTkLabel(
            self.main_frame,
            text=text,
            font=("Segoe UI", font_size),
            text_color="#333333"
        )
        label.place(x=pos[0], y=pos[1])

    def _render_image(self, element: Dict[str, Any], pos: tuple):
        """Render a static image."""
        image_path = element.get("image")
        image = self._load_image(image_path)

        if image:
            label = ctk.CTkLabel(self.main_frame, image=image, text="")
            label.place(x=pos[0] - image._size[0]//2, y=pos[1] - image._size[1]//2)

    def _render_client_table(self, element: Dict[str, Any], pos: tuple):
        """Render the client manager table."""
        row_height = element.get("row_height", 25)
        columns = element.get("columns", [])
        col_widths = element.get("column_widths", [100] * len(columns))

        # Header
        x = pos[0]
        for i, col in enumerate(columns):
            header = ctk.CTkLabel(
                self.main_frame,
                text=col,
                font=("Segoe UI", 12, "bold"),
                width=col_widths[i],
                anchor="w"
            )
            header.place(x=x, y=pos[1])
            x += col_widths[i] + 10

        # Rows
        y = pos[1] + row_height + 5
        for client in MOCK_CLIENTS:
            x = pos[0]

            # Client name (clickable)
            name_btn = ctk.CTkButton(
                self.main_frame,
                text=client.name,
                font=("Segoe UI", 11),
                width=col_widths[0],
                height=row_height,
                anchor="w",
                fg_color="transparent",
                text_color="#0066cc",
                hover_color="#e8f4fc",
                command=lambda c=client: self._on_client_double_click(c)
            )
            name_btn.place(x=x, y=y)
            x += col_widths[0] + 10

            # Return type
            type_label = ctk.CTkLabel(
                self.main_frame,
                text=client.return_type,
                font=("Segoe UI", 11),
                width=col_widths[1],
                anchor="w"
            )
            type_label.place(x=x, y=y)
            x += col_widths[1] + 10

            # Fed EF Status
            status_label = ctk.CTkLabel(
                self.main_frame,
                text=client.fed_ef_status or "(empty)",
                font=("Segoe UI", 11),
                width=col_widths[2],
                anchor="w",
                text_color="#666666" if not client.fed_ef_status else "#333333"
            )
            status_label.place(x=x, y=y)

            y += row_height + 2

    def _on_client_double_click(self, client: MockClient):
        """Handle double-click on client row."""
        logger.info(f"Client selected: {client.name} ({client.return_type})")
        self.selected_client = client
        self.current_return_type = client.return_type
        self.screens = get_screens(client.return_type)
        # Stay on client_manager - bot will click E-File menu
        self._render_screen()

    def _on_button_click(self, next_screen: Optional[str], action: Optional[str]):
        """Handle button click."""
        if action:
            logger.info(f"Action: {action}")
            # Handle special actions
            if action == "select_extension":
                pass  # Just visual feedback

        if next_screen:
            logger.info(f"Navigating to: {next_screen}")
            self.current_screen = next_screen
            self._render_screen()

    def _render_debug_info(self, elements: List[Dict[str, Any]]):
        """Render debug overlay showing element positions."""
        for element in elements:
            pos = element.get("position") or element.get("label_position")
            if pos:
                # Draw crosshair at position
                size = 10

                # Horizontal line
                h_line = ctk.CTkFrame(self.main_frame, width=size*2, height=1, fg_color="red")
                h_line.place(x=pos[0]-size, y=pos[1])

                # Vertical line
                v_line = ctk.CTkFrame(self.main_frame, width=1, height=size*2, fg_color="red")
                v_line.place(x=pos[0], y=pos[1]-size)

                # Position label
                pos_label = ctk.CTkLabel(
                    self.main_frame,
                    text=f"({pos[0]},{pos[1]})",
                    font=("Consolas", 8),
                    text_color="red",
                    fg_color="#ffffff"
                )
                pos_label.place(x=pos[0]+5, y=pos[1]+5)


def main():
    """Run the TaxAct Simulator."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )

    logger.info("Starting TaxAct Simulator")

    app = TaxActSimulator()
    app.mainloop()

    logger.info("TaxAct Simulator closed")


if __name__ == "__main__":
    main()
```

---

### Task 5: UPDATE config/settings.json

- **IMPLEMENT**: `mock_mode` Flag hinzufügen
- **PATTERN**: Bestehende Struktur
- **VALIDATE**: `python -c "import json; s=json.load(open('config/settings.json')); print('mock_mode:', s.get('mock_mode', False))"`

Füge am Anfang hinzu:
```json
{
  "mock_mode": false,
  "dev_mode": true,
  ...
}
```

---

### Task 6: CREATE Manual Test Script

- **IMPLEMENT**: Test-Script um Simulator und Bot zu starten
- **VALIDATE**: `python tests/manual/test_simulator.py`

```python
"""Test script for TaxAct Simulator.

Usage:
    1. Run this script to start the simulator
    2. In another terminal, run: python -m clickbot.gui
    3. The bot should interact with the simulator
"""

import subprocess
import sys
import time


def main():
    print("=" * 60)
    print("TaxAct Simulator Test")
    print("=" * 60)

    print("\n[1/2] Starting TaxAct Simulator...")
    print("      The simulator window will open at 1920x1080")
    print()
    print("INSTRUCTIONS:")
    print("  1. Position the simulator window at (0,0) - top-left of primary monitor")
    print("  2. In a NEW terminal, run: python -m clickbot.gui")
    print("  3. Click 'Start Bot' and watch it interact with the simulator")
    print()
    print("Press Ctrl+C to stop the simulator.")
    print()

    # Start simulator
    try:
        subprocess.run([sys.executable, "-m", "simulator.taxact_simulator"])
    except KeyboardInterrupt:
        print("\nSimulator stopped.")


if __name__ == "__main__":
    main()
```

---

## TESTING STRATEGY

### Unit Tests

- `test_mock_data.py`: Verify mock client data structure
- `test_screens.py`: Verify all screens have required elements

### Integration Tests

- Run simulator and verify each screen renders
- Verify button clicks navigate to correct screens
- Verify checkbox toggle works

### E2E Tests (Bot + Simulator)

1. Start Simulator
2. Start Bot GUI
3. Click "Start Bot"
4. Verify bot completes all 36 steps
5. Verify bot ends on Client Manager

---

## VALIDATION COMMANDS

### Level 1: Syntax & Imports

```bash
python -c "from simulator import taxact_simulator; print('OK')"
python -c "from simulator.screens import SCREENS_1120; print(len(SCREENS_1120), 'screens')"
python -c "from simulator.mock_data import MOCK_CLIENTS; print(len(MOCK_CLIENTS), 'clients')"
```

### Level 2: Run Simulator

```bash
python -m simulator.taxact_simulator
```

### Level 3: Bot Integration

```bash
# Terminal 1: Start simulator
python -m simulator.taxact_simulator

# Terminal 2: Start bot
python -m clickbot.gui
```

---

## ACCEPTANCE CRITERIA

- [ ] Simulator startet als 1920x1080 Fenster
- [ ] Client Manager zeigt Mock-Clients mit Return Type und Fed EF Status
- [ ] Alle 36 Screens des 1120-Prozesses sind definiert
- [ ] Buttons zeigen echte Screenshot-Bilder
- [ ] Template Matching des Bots findet die Buttons im Simulator
- [ ] Navigation durch alle Screens funktioniert
- [ ] Checkboxen können toggled werden
- [ ] Textfelder akzeptieren Eingabe
- [ ] Conditional Screen (Alerts Result) zeigt Pass/Fail basierend auf Toggle
- [ ] Debug-Overlay zeigt Element-Positionen
- [ ] Bot kann vollständigen 1120-Prozess gegen Simulator ausführen

---

## COMPLETION CHECKLIST

- [ ] `simulator/__init__.py` erstellt
- [ ] `simulator/mock_data.py` erstellt
- [ ] `simulator/screens.py` mit allen 36 Screens erstellt
- [ ] `simulator/taxact_simulator.py` erstellt
- [ ] Simulator startet ohne Fehler
- [ ] Alle Button-Bilder werden geladen
- [ ] Navigation funktioniert
- [ ] Bot findet Buttons via Template Matching
- [ ] Vollständiger E2E-Test erfolgreich

---

## NOTES

### Design-Entscheidungen

1. **Echte Screenshots als UI-Elemente**: Der Simulator verwendet die gleichen PNG-Dateien, die der Bot sucht. Dadurch findet Template Matching die Buttons.

2. **Screen-basierte Navigation**: Jeder "Screen" ist ein Zustand mit definierten Elementen. Button-Klicks wechseln zwischen Screens.

3. **Mock-Daten konfigurierbar**: Client-Liste kann für verschiedene Test-Szenarien angepasst werden.

4. **Debug-Overlay**: Zeigt Element-Positionen zur Kalibrierung an.

5. **Alerts Toggle**: Ermöglicht Testen des Error-Pfads ohne Code-Änderung.

### Erweiterungen für 1120S

Nach erfolgreicher 1120-Implementierung:
1. `SCREENS_1120S` in `screens.py` definieren
2. Unterschiedliche Screens für 1120S hinzufügen
3. Return-Type-basierte Screen-Auswahl bereits implementiert

### Bekannte Limitierungen

- Simulator muss manuell auf Primary Monitor positioniert werden
- Scrolling in Tax Liability Screen ist simuliert (Button erscheint direkt)
- Keine Persistenz zwischen Simulator-Neustarts

---

## CONFIDENCE SCORE: 9/10

**Gründe:**
- Klares Konzept: Screenshots als UI-Elemente
- CustomTkinter-Pattern bereits bekannt aus gui.py
- Screen-Definitionen basieren auf existierendem 1120.json
- Mock-Daten sind einfach anzupassen
- Debug-Overlay hilft bei Kalibrierung

**Risiko:**
- Button-Positionen müssen exakt stimmen für Template Matching
- Simulator-Fenster muss richtig positioniert sein

---

*Plan erstellt: 2026-02-10*
*Basierend auf PRD v2.3 und Phase 3 Implementation*
