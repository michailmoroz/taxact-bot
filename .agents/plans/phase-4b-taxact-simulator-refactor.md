# Feature: Phase 4b - TaxAct Simulator Refactor (Echte GUI ohne Screenshots)

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

## Feature Description

Komplette Neuimplementierung des TaxAct Simulators als **echte GUI-Anwendung** die TaxAct 2025 Professional visuell nachbildet. Statt Screenshots als UI-Elemente zu verwenden, werden echte CustomTkinter-Widgets mit TaxAct-ähnlichem Styling erstellt.

**Kern-Änderungen:**
- Styled Buttons (blau, grün) statt PNG-Bilder
- Echtes `ttk.Treeview` für Client Manager Tabelle mit Doppelklick-Support
- Echte `Toplevel` Popup-Fenster die sich öffnen/schließen
- True Fullscreen-Modus
- TaxAct-ähnliches visuelles Design (Farben, Fonts, Layout)

## User Story

As a **Entwickler** I want to **den Bot gegen eine visuell korrekte TaxAct-Simulation testen** so that **ich die Automatisierung entwickeln und debuggen kann, mit einer GUI die wie TaxAct aussieht und sich verhält**.

## Problem Statement

Die Phase-4 Implementation verwendete Screenshots als Button-Bilder, was zu:
- Korrupten/fehlerhaften Button-Darstellungen führte
- Keiner funktionierenden Bot-Integration (Template Matching findet nichts)
- Keinem echten Fullscreen-Modus
- Keiner echten Tabelle für Doppelklick-Interaktion

## Solution Statement

Kompletter Refactor des Simulators mit:
1. **Styled CTkButtons** die wie TaxAct-Buttons aussehen (Farben aus Screenshots extrahiert)
2. **ttk.Treeview** für die Client Manager Tabelle mit echten Spalten und Doppelklick
3. **Toplevel Popups** für E-File Center und andere Dialoge
4. **Fullscreen** via `attributes('-fullscreen', True)` oder maximiert

## Feature Metadata

**Feature Type**: Refactor/Enhancement
**Estimated Complexity**: Medium-High
**Primary Systems Affected**: `simulator/taxact_simulator.py`, `simulator/screens.py`
**Dependencies**: CustomTkinter (bereits vorhanden), tkinter.ttk (Standard)

---

## CONTEXT REFERENCES

### Relevant Codebase Files (MUST READ BEFORE IMPLEMENTING!)

| File | Lines | Why |
|------|-------|-----|
| `simulator/taxact_simulator.py` | Full | Aktuelle Implementation - komplett neu schreiben |
| `simulator/screens.py` | Full | Screen-Definitionen - Struktur anpassen |
| `simulator/mock_data.py` | Full | Mock-Daten - bleibt unverändert |
| `clickbot/gui.py` | 1-100 | CustomTkinter Pattern-Referenz |

### Screenshot-Referenzen für Design

| Screenshot | Zweck |
|------------|-------|
| `common/continue_blue.png` | Blauer Button: ~#2563EB, abgerundete Ecken, weißer Text "Continue" |
| `common/yes_green.png` | Grüner Button: ~#22C55E, abgerundete Ecken, weißer Text "Yes" |
| `common/client_manager_table.png` | Tabellen-Layout: Spalten, Fonts, Farben |

### Files to Modify

| File | Changes |
|------|---------|
| `simulator/taxact_simulator.py` | Komplette Neuimplementierung |
| `simulator/screens.py` | Button-Definitionen ohne image-Pfade |

### TaxAct Design-Spezifikationen (aus Screenshots extrahiert)

```python
# Farben
TAXACT_BLUE = "#2563EB"          # Continue Button
TAXACT_BLUE_HOVER = "#1D4ED8"    # Hover-Zustand
TAXACT_GREEN = "#22C55E"         # Yes Button
TAXACT_GREEN_HOVER = "#16A34A"   # Hover-Zustand
TAXACT_GRAY_BG = "#F3F4F6"       # Hintergrund
TAXACT_WHITE = "#FFFFFF"         # Content-Bereich
TAXACT_HEADER_BG = "#1E3A5F"     # Header-Leiste (dunkelblau)
TAXACT_TEXT = "#1F2937"          # Normaler Text
TAXACT_LINK = "#2563EB"          # Links/Klickbare Items

# Fonts
FONT_HEADER = ("Segoe UI", 14, "bold")
FONT_NORMAL = ("Segoe UI", 11)
FONT_BUTTON = ("Segoe UI", 11, "bold")

# Tabelle
TABLE_ROW_HEIGHT = 25
TABLE_HEADER_BG = "#F9FAFB"
TABLE_ALTERNATING_ROW = "#F3F4F6"
```

---

## IMPLEMENTATION PLAN

### Phase 1: Neue Screen-Definition Struktur

Ändern der `screens.py` um Buttons mit Text, Farben und Größen zu definieren statt mit Bild-Pfaden.

### Phase 2: TaxActSimulator Neuimplementierung

Komplett neue `taxact_simulator.py` mit:
- TaxAct-ähnlichem Header mit Tabs
- Echtem Treeview für Client-Tabelle
- Styled Buttons
- Toplevel Popups
- Fullscreen-Support

### Phase 3: Integration & Testing

Bot gegen neue Simulation testen.

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

---

### Task 1: UPDATE simulator/screens.py - Neue Button-Helper-Funktion

- **IMPLEMENT**: Neue `_btn()` Funktion die Text, Farbe, Größe definiert statt Bild-Pfad
- **PATTERN**: Bestehende Helper-Funktionen
- **VALIDATE**: `python -c "from simulator.screens import _btn; print(_btn('Continue', (850, 650), 'blue'))"`

**Alte Signatur:**
```python
def _btn(image: str, pos: tuple, next_screen: str = None, action: str = None)
```

**Neue Signatur:**
```python
def _btn(text: str, pos: tuple, color: str = "blue", width: int = 100, height: int = 35,
         next_screen: str = None, action: str = None) -> Dict[str, Any]:
    """Helper to create styled button element.

    Args:
        text: Button text (e.g., "Continue", "Yes")
        pos: (x, y) position on screen
        color: "blue", "green", "gray", or hex color
        width: Button width in pixels
        height: Button height in pixels
        next_screen: Screen to navigate to on click
        action: Special action to trigger
    """
    return {
        "type": "button",
        "text": text,
        "position": pos,
        "color": color,
        "width": width,
        "height": height,
        "next_screen": next_screen,
        "action": action
    }
```

---

### Task 2: UPDATE simulator/screens.py - Neue Checkbox-Helper-Funktion

- **IMPLEMENT**: Checkbox mit Text statt Bildern
- **VALIDATE**: `python -c "from simulator.screens import _checkbox; print(_checkbox('Homeowners Association', (400, 300)))"`

**Neue Signatur:**
```python
def _checkbox(label: str, pos: tuple, default_checked: bool = False,
              checkbox_id: str = None) -> Dict[str, Any]:
    """Helper to create checkbox element.

    Args:
        label: Text label for checkbox
        pos: (x, y) position
        default_checked: Initial state
        checkbox_id: Unique ID for state tracking
    """
    return {
        "type": "checkbox",
        "label": label,
        "position": pos,
        "checked": default_checked,
        "checkbox_id": checkbox_id
    }
```

---

### Task 3: UPDATE simulator/screens.py - Neue Textfield-Helper-Funktion

- **IMPLEMENT**: Textfield mit Text-Label statt Bild-Label
- **VALIDATE**: `python -c "from simulator.screens import _textfield; print(_textfield('Title:', (200, 200), 'officer_title'))"`

**Neue Signatur:**
```python
def _textfield(label: str, pos: tuple, field_id: str,
               field_width: int = 200, field_height: int = 30) -> Dict[str, Any]:
    """Helper to create labeled textfield element.

    Args:
        label: Text label (e.g., "Title:", "Email:")
        pos: (x, y) position for label
        field_id: Unique ID for value storage
        field_width: Width of input field
        field_height: Height of input field
    """
    return {
        "type": "textfield",
        "label": label,
        "position": pos,
        "field_id": field_id,
        "field_width": field_width,
        "field_height": field_height
    }
```

---

### Task 4: UPDATE simulator/screens.py - SCREENS_1120 aktualisieren

- **IMPLEMENT**: Alle 26 Screens mit neuen Helper-Funktionen umschreiben
- **PATTERN**: Neue Helper-Signaturen aus Tasks 1-3
- **VALIDATE**: `python -c "from simulator.screens import SCREENS_1120; print(len(SCREENS_1120), 'screens')"`

**Beispiel-Umwandlung:**

Alt:
```python
_btn("common/continue_blue.png", (850, 650), next_screen="federal_extension")
```

Neu:
```python
_btn("Continue", (850, 650), color="blue", width=120, height=40, next_screen="federal_extension")
```

**Wichtige Button-Mappings:**

| Alter Image-Pfad | Neuer Text | Farbe | Größe |
|------------------|------------|-------|-------|
| `common/continue_blue.png` | "Continue" | blue | 120x40 |
| `common/continue_green.png` | "Continue" | green | 120x40 |
| `common/yes_green.png` | "Yes" | green | 80x35 |
| `common/efile_menu.png` | "E-file" | blue | 80x30 |
| `common/clients_button.png` | "Clients" | gray | 80x30 |
| `common/submit_electronic_filing.png` | "Submit Electronic Filing Return" | blue | 250x40 |
| `common/popup_close_x.png` | "X" | gray | 30x30 |
| `1120/complete_form_7004.png` | "Complete Form 7004" | blue | 180x40 |
| `1120/efile_form_7004.png` | "E-file Form 7004" | blue | 150x40 |
| `1120/start_form_7004_alerts.png` | "Start Form 7004 Alerts" | blue | 200x40 |
| `1120/submit_efile.png` | "Submit" | green | 100x40 |
| `common/new_return.png` | "New Return" | blue | 120x40 |

---

### Task 5: CREATE simulator/styles.py - TaxAct Style-Konstanten

- **IMPLEMENT**: Zentrale Style-Definitionen
- **VALIDATE**: `python -c "from simulator.styles import TAXACT_BLUE, BUTTON_STYLES; print(TAXACT_BLUE)"`

```python
"""TaxAct visual style constants.

Colors and fonts extracted from TaxAct 2025 screenshots.
"""

# =============================================================================
# COLORS
# =============================================================================

# Primary Colors
TAXACT_BLUE = "#2563EB"
TAXACT_BLUE_HOVER = "#1D4ED8"
TAXACT_BLUE_DARK = "#1E3A5F"  # Header

TAXACT_GREEN = "#22C55E"
TAXACT_GREEN_HOVER = "#16A34A"

# Grays
TAXACT_GRAY = "#6B7280"
TAXACT_GRAY_LIGHT = "#F3F4F6"
TAXACT_GRAY_HOVER = "#E5E7EB"

# Background
TAXACT_BG = "#F3F4F6"
TAXACT_WHITE = "#FFFFFF"

# Text
TAXACT_TEXT_PRIMARY = "#1F2937"
TAXACT_TEXT_SECONDARY = "#6B7280"
TAXACT_LINK = "#2563EB"

# Table
TABLE_HEADER_BG = "#F9FAFB"
TABLE_ROW_ALT = "#F3F4F6"
TABLE_BORDER = "#E5E7EB"

# =============================================================================
# FONTS
# =============================================================================

FONT_FAMILY = "Segoe UI"

FONT_HEADER = (FONT_FAMILY, 16, "bold")
FONT_TITLE = (FONT_FAMILY, 14, "bold")
FONT_NORMAL = (FONT_FAMILY, 11)
FONT_BUTTON = (FONT_FAMILY, 11)
FONT_SMALL = (FONT_FAMILY, 10)

# =============================================================================
# BUTTON STYLES
# =============================================================================

BUTTON_STYLES = {
    "blue": {
        "fg_color": TAXACT_BLUE,
        "hover_color": TAXACT_BLUE_HOVER,
        "text_color": "#FFFFFF",
        "corner_radius": 6
    },
    "green": {
        "fg_color": TAXACT_GREEN,
        "hover_color": TAXACT_GREEN_HOVER,
        "text_color": "#FFFFFF",
        "corner_radius": 6
    },
    "gray": {
        "fg_color": TAXACT_GRAY_LIGHT,
        "hover_color": TAXACT_GRAY_HOVER,
        "text_color": TAXACT_TEXT_PRIMARY,
        "corner_radius": 6
    }
}

# =============================================================================
# LAYOUT
# =============================================================================

HEADER_HEIGHT = 50
TAB_HEIGHT = 40
TABLE_ROW_HEIGHT = 28
CONTENT_PADDING = 20
```

---

### Task 6: REWRITE simulator/taxact_simulator.py - Basis-Struktur

- **IMPLEMENT**: Neue Hauptklasse mit Fullscreen, Header, Content-Area
- **VALIDATE**: `python -c "from simulator.taxact_simulator import TaxActSimulator; print('OK')"`

**Neue Struktur:**

```python
"""TaxAct Simulator - Mock GUI for testing the automation bot.

A proper GUI application that mimics TaxAct 2025 Professional
using styled widgets instead of screenshots.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional

import customtkinter as ctk

from simulator.screens import SCREENS_1120, SCREENS_1120S, get_screens
from simulator.mock_data import MOCK_CLIENTS, MockClient
from simulator.styles import *

logger = logging.getLogger(__name__)

ctk.set_appearance_mode("light")


class TaxActSimulator(ctk.CTk):
    """TaxAct 2025 Professional Simulator."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("TaxAct 2025 Professional Edition - Client Manager")
        self._setup_fullscreen()

        # State
        self.current_screen = "client_manager"
        self.current_return_type = "1120"
        self.screens = get_screens(self.current_return_type)
        self.selected_client: Optional[MockClient] = None
        self.textfield_values: Dict[str, str] = {}
        self.checkbox_states: Dict[str, bool] = {}
        self.alerts_passed = True

        # Active popups
        self.active_popup: Optional[ctk.CTkToplevel] = None

        # Build UI
        self._create_header()
        self._create_tabs()
        self._create_content_area()
        self._create_status_bar()

        # Render initial screen
        self._render_screen()

        logger.info("TaxAct Simulator initialized")

    def _setup_fullscreen(self):
        """Setup fullscreen or maximized window."""
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Set geometry to full screen size
        self.geometry(f"{screen_width}x{screen_height}+0+0")

        # Try to maximize (Windows)
        try:
            self.state('zoomed')
        except:
            # Fallback for other platforms
            self.attributes('-fullscreen', False)

        self.resizable(True, True)
```

---

### Task 7: IMPLEMENT simulator/taxact_simulator.py - Header und Tabs

- **IMPLEMENT**: TaxAct-ähnlicher Header mit Menü und Tabs
- **PATTERN**: Siehe `client_manager_table.png` für Layout

```python
    def _create_header(self):
        """Create TaxAct-style header bar."""
        self.header_frame = ctk.CTkFrame(
            self,
            height=HEADER_HEIGHT,
            fg_color=TAXACT_BLUE_DARK,
            corner_radius=0
        )
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False)

        # Logo/Title
        title_label = ctk.CTkLabel(
            self.header_frame,
            text="TaxAct 2025 Professional Edition - [Simulator]",
            font=FONT_HEADER,
            text_color="#FFFFFF"
        )
        title_label.pack(side="left", padx=20, pady=10)

    def _create_tabs(self):
        """Create tab bar like TaxAct."""
        self.tab_frame = ctk.CTkFrame(
            self,
            height=TAB_HEIGHT,
            fg_color=TAXACT_WHITE,
            corner_radius=0
        )
        self.tab_frame.pack(fill="x", side="top")
        self.tab_frame.pack_propagate(False)

        # Tabs
        tabs = ["Client Manager", "eSignatures", "Appointments",
                "Professional Reports", "Documents", "Notifications"]

        for i, tab_name in enumerate(tabs):
            is_active = (tab_name == "Client Manager")
            tab_btn = ctk.CTkButton(
                self.tab_frame,
                text=tab_name,
                font=FONT_NORMAL,
                fg_color=TAXACT_BLUE if is_active else "transparent",
                text_color="#FFFFFF" if is_active else TAXACT_TEXT_PRIMARY,
                hover_color=TAXACT_BLUE_HOVER if is_active else TAXACT_GRAY_LIGHT,
                corner_radius=0,
                width=120,
                height=TAB_HEIGHT - 5
            )
            tab_btn.pack(side="left", padx=2, pady=2)
```

---

### Task 8: IMPLEMENT simulator/taxact_simulator.py - Client Table mit ttk.Treeview

- **IMPLEMENT**: Echte Tabelle mit Spalten und Doppelklick-Support
- **PATTERN**: TaxAct Client Manager aus Screenshot
- **VALIDATE**: Simulator starten, Tabelle anzeigen, Doppelklick testen

```python
    def _create_client_table(self):
        """Create the client manager table using ttk.Treeview."""
        # Table frame
        table_frame = ctk.CTkFrame(self.content_frame, fg_color=TAXACT_WHITE)
        table_frame.pack(fill="both", expand=True, padx=CONTENT_PADDING, pady=10)

        # Configure ttk style for Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=TAXACT_WHITE,
            foreground=TAXACT_TEXT_PRIMARY,
            rowheight=TABLE_ROW_HEIGHT,
            fieldbackground=TAXACT_WHITE,
            font=FONT_NORMAL
        )
        style.configure(
            "Treeview.Heading",
            background=TABLE_HEADER_BG,
            foreground=TAXACT_TEXT_PRIMARY,
            font=FONT_TITLE
        )
        style.map("Treeview", background=[("selected", TAXACT_BLUE)])

        # Columns
        columns = ("client", "ssn", "return_type", "return_status", "fed_ef_status")

        self.client_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Define headings
        self.client_tree.heading("client", text="Client")
        self.client_tree.heading("ssn", text="SSN/EIN")
        self.client_tree.heading("return_type", text="Return Type")
        self.client_tree.heading("return_status", text="Return Status")
        self.client_tree.heading("fed_ef_status", text="Fed EF Status")

        # Define column widths
        self.client_tree.column("client", width=250, anchor="w")
        self.client_tree.column("ssn", width=100, anchor="w")
        self.client_tree.column("return_type", width=100, anchor="center")
        self.client_tree.column("return_status", width=100, anchor="center")
        self.client_tree.column("fed_ef_status", width=120, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.client_tree.yview)
        self.client_tree.configure(yscrollcommand=scrollbar.set)

        # Pack
        self.client_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind double-click
        self.client_tree.bind("<Double-1>", self._on_table_double_click)

        # Populate with mock data
        self._populate_client_table()

    def _populate_client_table(self):
        """Fill the table with mock client data."""
        # Clear existing
        for item in self.client_tree.get_children():
            self.client_tree.delete(item)

        # Add mock clients
        for client in MOCK_CLIENTS:
            self.client_tree.insert(
                "",
                "end",
                values=(
                    client.name,
                    "**-***1234",  # Masked SSN
                    client.return_type,
                    "Imported",
                    client.fed_ef_status or ""
                ),
                tags=(client.return_type,)
            )

    def _on_table_double_click(self, event):
        """Handle double-click on table row."""
        selection = self.client_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.client_tree.item(item, "values")
        client_name = values[0]
        return_type = values[2]

        # Find matching mock client
        for client in MOCK_CLIENTS:
            if client.name == client_name:
                self.selected_client = client
                self.current_return_type = client.return_type
                self.screens = get_screens(client.return_type)
                logger.info(f"Selected client: {client.name} ({client.return_type})")

                # Update window title
                self.title(f"TaxAct 2025 Professional Edition - {client.name}")
                break
```

---

### Task 9: IMPLEMENT simulator/taxact_simulator.py - Styled Buttons

- **IMPLEMENT**: Methode zum Rendern von Buttons mit TaxAct-Styling
- **PATTERN**: Farben aus `styles.py`

```python
    def _render_button(self, element: Dict[str, Any], parent: ctk.CTkFrame):
        """Render a styled button."""
        text = element.get("text", "Button")
        pos = element.get("position", (0, 0))
        color = element.get("color", "blue")
        width = element.get("width", 100)
        height = element.get("height", 35)
        next_screen = element.get("next_screen")
        action = element.get("action")

        # Get style
        style = BUTTON_STYLES.get(color, BUTTON_STYLES["blue"])

        btn = ctk.CTkButton(
            parent,
            text=text,
            font=FONT_BUTTON,
            width=width,
            height=height,
            fg_color=style["fg_color"],
            hover_color=style["hover_color"],
            text_color=style["text_color"],
            corner_radius=style["corner_radius"],
            command=lambda: self._on_button_click(next_screen, action)
        )

        # Place at position
        btn.place(x=pos[0], y=pos[1])

        return btn
```

---

### Task 10: IMPLEMENT simulator/taxact_simulator.py - Toplevel Popups

- **IMPLEMENT**: Echte Popup-Fenster für E-File Center etc.
- **PATTERN**: tkinter Toplevel

```python
    def _show_popup(self, screen_name: str):
        """Show a popup window for the given screen."""
        screen_def = self.screens.get(screen_name)
        if not screen_def:
            return

        # Close existing popup
        if self.active_popup:
            self.active_popup.destroy()

        # Create popup
        popup = ctk.CTkToplevel(self)
        popup.title(screen_def.get("title", "Dialog"))
        popup.geometry("600x400")
        popup.transient(self)  # Stay on top of main window
        popup.grab_set()  # Modal

        # Center on screen
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() - 600) // 2
        y = (popup.winfo_screenheight() - 400) // 2
        popup.geometry(f"+{x}+{y}")

        # Store reference
        self.active_popup = popup
        self.current_screen = screen_name

        # Render popup content
        self._render_popup_content(popup, screen_def)

        # Handle close
        popup.protocol("WM_DELETE_WINDOW", self._close_popup)

    def _close_popup(self):
        """Close the active popup and return to client manager."""
        if self.active_popup:
            self.active_popup.destroy()
            self.active_popup = None
        self.current_screen = "client_manager"
        self._render_screen()

    def _render_popup_content(self, popup: ctk.CTkToplevel, screen_def: Dict[str, Any]):
        """Render content inside a popup window."""
        # Title
        title = screen_def.get("title", "")
        title_label = ctk.CTkLabel(
            popup,
            text=title,
            font=FONT_HEADER,
            text_color=TAXACT_TEXT_PRIMARY
        )
        title_label.pack(pady=20)

        # Content frame
        content = ctk.CTkFrame(popup, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=10)

        # Render elements
        for element in screen_def.get("elements", []):
            self._render_element(element, content)
```

---

### Task 11: IMPLEMENT simulator/taxact_simulator.py - Screen Rendering

- **IMPLEMENT**: Komplette `_render_screen()` Methode für alle Element-Typen
- **VALIDATE**: Durch verschiedene Screens navigieren

```python
    def _create_content_area(self):
        """Create the main content area."""
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color=TAXACT_BG,
            corner_radius=0
        )
        self.content_frame.pack(fill="both", expand=True)

    def _clear_content(self):
        """Clear the content area."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _render_screen(self):
        """Render the current screen."""
        self._clear_content()

        screen_def = self.screens.get(self.current_screen)
        if not screen_def:
            logger.error(f"Unknown screen: {self.current_screen}")
            return

        # Check if popup
        if screen_def.get("is_popup"):
            self._show_popup(self.current_screen)
            return

        # Handle conditional screens
        if screen_def.get("conditional"):
            condition_var = screen_def.get("condition_var")
            if condition_var == "alerts_passed":
                elements = screen_def.get(
                    "elements_if_true" if self.alerts_passed else "elements_if_false",
                    []
                )
            else:
                elements = screen_def.get("elements", [])
        else:
            elements = screen_def.get("elements", [])

        # Special handling for client_manager
        if self.current_screen == "client_manager":
            self._render_client_manager()
            return

        # Render standard screen
        self._render_standard_screen(screen_def, elements)

    def _render_client_manager(self):
        """Render the client manager screen with table."""
        # Toolbar with buttons
        toolbar = ctk.CTkFrame(self.content_frame, height=50, fg_color=TAXACT_WHITE)
        toolbar.pack(fill="x", padx=CONTENT_PADDING, pady=10)

        # Add Client button
        add_btn = ctk.CTkButton(
            toolbar,
            text="+ Add Client",
            font=FONT_BUTTON,
            fg_color=TAXACT_GREEN,
            hover_color=TAXACT_GREEN_HOVER,
            text_color="#FFFFFF",
            width=120,
            height=35
        )
        add_btn.pack(side="left", padx=5)

        # E-file button
        efile_btn = ctk.CTkButton(
            toolbar,
            text="E-file",
            font=FONT_BUTTON,
            fg_color=TAXACT_BLUE,
            hover_color=TAXACT_BLUE_HOVER,
            text_color="#FFFFFF",
            width=80,
            height=35,
            command=lambda: self._on_button_click("efile_popup", None)
        )
        efile_btn.pack(side="left", padx=5)

        # Create table
        self._create_client_table()

    def _render_standard_screen(self, screen_def: Dict[str, Any], elements: List[Dict]):
        """Render a standard (non-table) screen."""
        # Title
        title = screen_def.get("title", "")
        if title:
            title_label = ctk.CTkLabel(
                self.content_frame,
                text=title,
                font=FONT_HEADER,
                text_color=TAXACT_TEXT_PRIMARY
            )
            title_label.pack(pady=30)

        # Content panel (white background)
        panel = ctk.CTkFrame(
            self.content_frame,
            fg_color=TAXACT_WHITE,
            corner_radius=10
        )
        panel.pack(fill="both", expand=True, padx=50, pady=20)

        # Render elements
        for element in elements:
            self._render_element(element, panel)

    def _render_element(self, element: Dict[str, Any], parent: ctk.CTkFrame):
        """Render a single UI element."""
        elem_type = element.get("type")

        if elem_type == "button":
            self._render_button(element, parent)
        elif elem_type == "checkbox":
            self._render_checkbox(element, parent)
        elif elem_type == "textfield":
            self._render_textfield(element, parent)
        elif elem_type == "label":
            self._render_label(element, parent)
```

---

### Task 12: IMPLEMENT simulator/taxact_simulator.py - Checkbox und Textfield

- **IMPLEMENT**: Checkbox und Textfield Rendering

```python
    def _render_checkbox(self, element: Dict[str, Any], parent: ctk.CTkFrame):
        """Render a checkbox."""
        label = element.get("label", "Checkbox")
        pos = element.get("position", (0, 0))
        checkbox_id = element.get("checkbox_id", f"cb_{pos}")
        default_checked = element.get("checked", False)

        # Get or set state
        if checkbox_id not in self.checkbox_states:
            self.checkbox_states[checkbox_id] = default_checked

        var = ctk.BooleanVar(value=self.checkbox_states[checkbox_id])

        cb = ctk.CTkCheckBox(
            parent,
            text=label,
            font=FONT_NORMAL,
            variable=var,
            command=lambda: self._on_checkbox_change(checkbox_id, var.get()),
            fg_color=TAXACT_BLUE,
            hover_color=TAXACT_BLUE_HOVER
        )
        cb.place(x=pos[0], y=pos[1])

    def _on_checkbox_change(self, checkbox_id: str, value: bool):
        """Handle checkbox state change."""
        self.checkbox_states[checkbox_id] = value

    def _render_textfield(self, element: Dict[str, Any], parent: ctk.CTkFrame):
        """Render a labeled text field."""
        label_text = element.get("label", "Field:")
        pos = element.get("position", (0, 0))
        field_id = element.get("field_id", "unknown")
        width = element.get("field_width", 200)
        height = element.get("field_height", 30)

        # Label
        label = ctk.CTkLabel(
            parent,
            text=label_text,
            font=FONT_NORMAL,
            text_color=TAXACT_TEXT_PRIMARY
        )
        label.place(x=pos[0], y=pos[1])

        # Entry field
        entry = ctk.CTkEntry(
            parent,
            width=width,
            height=height,
            font=FONT_NORMAL,
            border_color=TABLE_BORDER,
            fg_color=TAXACT_WHITE
        )
        entry.place(x=pos[0] + 150, y=pos[1])

        # Restore value
        if field_id in self.textfield_values:
            entry.insert(0, self.textfield_values[field_id])

        # Save on change
        entry.bind("<KeyRelease>", lambda e: self._save_textfield(field_id, entry.get()))

    def _save_textfield(self, field_id: str, value: str):
        """Save textfield value."""
        self.textfield_values[field_id] = value

    def _render_label(self, element: Dict[str, Any], parent: ctk.CTkFrame):
        """Render a text label."""
        text = element.get("text", "")
        pos = element.get("position", (0, 0))
        font_size = element.get("font_size", 11)

        label = ctk.CTkLabel(
            parent,
            text=text,
            font=(FONT_FAMILY, font_size),
            text_color=TAXACT_TEXT_PRIMARY
        )
        label.place(x=pos[0], y=pos[1])
```

---

### Task 13: IMPLEMENT simulator/taxact_simulator.py - Status Bar und Main

- **IMPLEMENT**: Debug-Statusbar und main() Funktion

```python
    def _create_status_bar(self):
        """Create status bar at bottom."""
        self.status_frame = ctk.CTkFrame(
            self,
            height=30,
            fg_color=TAXACT_GRAY_LIGHT,
            corner_radius=0
        )
        self.status_frame.pack(fill="x", side="bottom")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text=f"Screen: {self.current_screen} | Client: None",
            font=FONT_SMALL,
            text_color=TAXACT_TEXT_SECONDARY
        )
        self.status_label.pack(side="left", padx=10)

        # Alerts toggle
        self.alerts_var = ctk.BooleanVar(value=True)
        alerts_cb = ctk.CTkCheckBox(
            self.status_frame,
            text="Alerts Pass",
            variable=self.alerts_var,
            command=self._on_alerts_toggle,
            font=FONT_SMALL
        )
        alerts_cb.pack(side="right", padx=10)

    def _update_status(self):
        """Update status bar text."""
        client_name = self.selected_client.name if self.selected_client else "None"
        self.status_label.configure(
            text=f"Screen: {self.current_screen} | Return: {self.current_return_type} | Client: {client_name}"
        )

    def _on_alerts_toggle(self):
        """Handle alerts toggle."""
        self.alerts_passed = self.alerts_var.get()
        if self.current_screen == "alerts_result":
            self._render_screen()

    def _on_button_click(self, next_screen: Optional[str], action: Optional[str]):
        """Handle button click."""
        if action:
            logger.info(f"Action: {action}")

        if next_screen:
            logger.info(f"Navigating to: {next_screen}")
            self.current_screen = next_screen
            self._update_status()
            self._render_screen()


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

### Task 14: UPDATE tests/manual/test_simulator.py

- **IMPLEMENT**: Aktualisiertes Test-Script mit Anleitung
- **VALIDATE**: `python tests/manual/test_simulator.py`

---

## TESTING STRATEGY

### Manual Testing

1. **Simulator starten**: `python -m simulator.taxact_simulator`
2. **Fullscreen** verifizieren - Fenster sollte maximiert sein
3. **Tabelle** prüfen:
   - Alle 10 Mock-Clients sichtbar
   - Spalten: Client, SSN/EIN, Return Type, Return Status, Fed EF Status
   - Doppelklick auf Client wählt ihn aus
4. **Navigation** testen:
   - E-file Button → Popup öffnet sich
   - Continue/Yes Buttons navigieren zu nächstem Screen
   - X Button schließt Popup
5. **Styling** verifizieren:
   - Blaue Buttons sind blau (#2563EB)
   - Grüne Buttons sind grün (#22C55E)
   - Fonts sind lesbar

### Bot Integration Testing

```bash
# Terminal 1: Simulator
python -m simulator.taxact_simulator

# Terminal 2: Bot
python -m clickbot.gui
```

Der Bot sollte:
- Client in Tabelle per Doppelklick auswählen können
- Durch Screens navigieren können (Koordinaten-basiert)

---

## VALIDATION COMMANDS

### Level 1: Syntax & Imports

```bash
python -m py_compile simulator/styles.py
python -m py_compile simulator/screens.py
python -m py_compile simulator/taxact_simulator.py
python -c "from simulator.styles import TAXACT_BLUE, BUTTON_STYLES; print('Styles OK')"
python -c "from simulator.screens import SCREENS_1120, _btn; print(len(SCREENS_1120), 'screens')"
python -c "from simulator.taxact_simulator import TaxActSimulator; print('Simulator OK')"
```

### Level 2: Run Simulator

```bash
python -m simulator.taxact_simulator
```

Erwartetes Verhalten:
- Fenster öffnet sich maximiert
- Client Manager Tabelle mit 10 Clients
- Blaue/Grüne Buttons sichtbar

---

## ACCEPTANCE CRITERIA

- [ ] Simulator startet im Fullscreen/Maximized-Modus
- [ ] Client Manager Tabelle zeigt alle 10 Mock-Clients
- [ ] Tabelle hat korrekte Spalten (Client, SSN, Return Type, Return Status, Fed EF Status)
- [ ] Doppelklick auf Client wählt ihn aus
- [ ] E-file Button öffnet Popup-Fenster
- [ ] Popup kann mit X geschlossen werden
- [ ] Alle Buttons haben TaxAct-ähnliches Styling (blau/grün)
- [ ] Navigation durch alle 26 Screens funktioniert
- [ ] Checkboxen können getoggelt werden
- [ ] Textfelder akzeptieren Eingabe
- [ ] Status Bar zeigt aktuellen Screen/Client

---

## COMPLETION CHECKLIST

- [ ] `simulator/styles.py` erstellt mit TaxAct-Farben
- [ ] `simulator/screens.py` aktualisiert (Text-basierte Buttons)
- [ ] `simulator/taxact_simulator.py` komplett neu geschrieben
- [ ] Fullscreen funktioniert
- [ ] Tabelle mit ttk.Treeview funktioniert
- [ ] Toplevel Popups funktionieren
- [ ] Styled Buttons sehen TaxAct-ähnlich aus
- [ ] Alle Syntax-Checks bestanden

---

## NOTES

### Design-Entscheidungen

1. **ttk.Treeview statt CTkTable**: Treeview ist Standard-tkinter, hat besseren Doppelklick-Support und ist robuster

2. **Toplevel für Popups**: Echte modale Fenster statt Screen-Wechsel im Hauptfenster

3. **Styled Buttons statt Bilder**: CTkButton mit Farben/Fonts die TaxAct nachahmen - keine Screenshots nötig

4. **Maximized statt Fullscreen**: `state('zoomed')` funktioniert besser auf Windows als `attributes('-fullscreen', True)`

### Bot-Integration

Der Bot verwendet:
1. **Koordinaten-Klicks**: Funktioniert weiterhin, da Buttons an denselben Positionen sind
2. **Template Matching**: Funktioniert NICHT mehr mit dieser Implementierung
3. **OCR für Tabelle**: Könnte funktionieren wenn Treeview-Text lesbar ist

Für volle Bot-Kompatibilität müsste der Bot auf koordinaten-basiertes Klicken umgestellt werden (ohne Template Matching).

---

## CONFIDENCE SCORE: 8/10

**Stärken:**
- Klare Struktur mit separaten Style-Definitionen
- Bewährte Patterns (Treeview, Toplevel)
- TaxAct-Design aus Screenshots extrahiert

**Risiken:**
- Bot-Integration erfordert möglicherweise Anpassungen
- ttk.Treeview Styling kann auf verschiedenen Systemen unterschiedlich aussehen
- Koordinaten müssen zu neuen Button-Positionen passen

---

*Plan erstellt: 2026-02-10*
*Basierend auf Phase-4 Lessons Learned und TaxAct Screenshot-Analyse*
