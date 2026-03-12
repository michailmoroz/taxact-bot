# Plan: GUI Redesign — Modern Dark UI

## User Story

Als Steuerberater möchte ich eine professionell gestaltete, moderne GUI, damit die Return-Type-Auswahl prominent sichtbar ist und die gesamte Anwendung visuell hochwertig wirkt.

## Acceptance Criteria

- [ ] Return Type Selector ist als Hero-Card der visuell prominenteste Bereich
- [ ] Alle Sections sind als Cards mit abgerundeten Ecken und subtilen Borders dargestellt
- [ ] Header ist kompakt (Icon + Titel in einer Zeile, kein eigener Frame)
- [ ] Font ist "Segoe UI" (Windows-System) mit klarer typografischer Hierarchie
- [ ] Start-Button verwendet sattes Grün (#22c55e) statt Neon-Grün
- [ ] Log-Bereich verwendet Monospace-Font (Cascadia Code / Consolas)
- [ ] Farbsystem: Elevation-Ladder (#1a1a1a → #242424 → #2e2e2e)
- [ ] **Keine Funktionalität geht verloren** — alle Widgets, State Machine, Lifecycle identisch

## Context

Die aktuelle GUI ist funktional korrekt, wirkt aber visuell flach und der Return-Type-Selector geht unter. Das Redesign führt ein Apple-inspiriertes Dark-Theme mit Card-Layout, besserer Typografie und prominenterem Return-Type-Selector ein. Nur `gui.py` wird geändert, keine Logik-Modifikationen.

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `clickbot/gui.py` | Einzige zu ändernde Datei — gesamte GUI | 1-444 |
| `config/settings.json` | GUI-Settings (window_width, window_height, etc.) | 42-48 |

### Patterns to Follow
- CustomTkinter Widget-Erstellung: `gui.py:81-158` (`_create_widgets`)
- Grid/Pack Layout: `gui.py:160-187` (`_setup_layout`)
- State Machine: `gui.py:203-291` (darf NICHT verändert werden)
- Bot Control: `gui.py:295-367` (darf NICHT verändert werden)
- Lifecycle: `gui.py:371-411` (darf NICHT verändert werden)
- `main()`: `gui.py:414-444` (darf NICHT verändert werden)

### Design Tokens (aus Research)

**Farben:**
```python
COLORS = {
    "bg_primary":     "#1a1a1a",  # Window background
    "bg_card":        "#242424",  # Card surfaces
    "bg_input":       "#2e2e2e",  # Nested elements, log textbox
    "border_subtle":  "#2e2e2e",  # Card borders
    "text_primary":   "#e5e5e5",  # Main text
    "text_secondary": "#999999",  # Labels, captions
    "text_muted":     "#666666",  # Disabled/placeholder
    "accent":         "#2563eb",  # Selected segment, highlights
    "accent_hover":   "#1d4ed8",  # Hover on accent
    "success":        "#22c55e",  # Start button
    "success_hover":  "#16a34a",  # Start hover
    "warning":        "#f59e0b",  # Cancel button
    "warning_hover":  "#d97706",  # Cancel hover
    "error":          "#ef4444",  # Stop button, error text
    "error_hover":    "#dc2626",  # Stop hover
}
```

**Fonts:**
```python
FONTS = {
    "title":     ("Segoe UI Semibold", 18),
    "section":   ("Segoe UI", 12),           # Section labels (muted)
    "selector":  ("Segoe UI Semibold", 15),  # Return Type buttons
    "button":    ("Segoe UI Semibold", 15),  # Start/Stop
    "body":      ("Segoe UI", 13),           # Status text
    "caption":   ("Segoe UI", 12),           # Secondary info
    "countdown": ("Segoe UI", 48),           # Countdown number
    "log":       ("Consolas", 12),           # Log monospace
}
```

**Spacing:**
```
Window padding:   24px
Card padding:     16px
Card gap:         12px
Card corner:      10px
Card border:      1px
Button height:    48px
Selector height:  42px
```

## Dependencies

- **New Packages**: none
- **Affected Modules**: `clickbot/gui.py` only
- **Breaking Changes**: No

## Tasks

### Task 1: ADD Design Constants to `gui.py`

- **Action**: ADD
- **Implement**: Add `COLORS`, `FONTS`, `SPACING`, `RADIUS` dictionaries at module level (after imports, before `GUIState` class). These replace all hardcoded color/font values throughout the file.
- **Pattern**: Module-level constants, similar to how `logger` is defined at `gui.py:23`
- **Depends on**: none
- **Validate**: `python -c "from clickbot.gui import COLORS, FONTS; print('OK')"`

```python
# --- Design Tokens ---

COLORS = {
    "bg_primary":     "#1a1a1a",
    "bg_card":        "#242424",
    "bg_input":       "#2e2e2e",
    "border_subtle":  "#2e2e2e",
    "text_primary":   "#e5e5e5",
    "text_secondary": "#999999",
    "text_muted":     "#666666",
    "accent":         "#2563eb",
    "accent_hover":   "#1d4ed8",
    "success":        "#22c55e",
    "success_hover":  "#16a34a",
    "warning":        "#f59e0b",
    "warning_hover":  "#d97706",
    "error":          "#ef4444",
    "error_hover":    "#dc2626",
}

FONTS = {
    "title":     ("Segoe UI Semibold", 18),
    "section":   ("Segoe UI", 12),
    "selector":  ("Segoe UI Semibold", 15),
    "button":    ("Segoe UI Semibold", 15),
    "body":      ("Segoe UI", 13),
    "caption":   ("Segoe UI", 12),
    "countdown": ("Segoe UI", 48),
    "log":       ("Consolas", 12),
}
```

### Task 2: UPDATE `_setup_window()` in `gui.py`

- **Action**: UPDATE
- **Implement**:
  - Set `self.configure(fg_color=COLORS["bg_primary"])` to enforce dark window background
  - Update `minsize` to `(420, 580)` for new layout
  - Row weights: keep row 4 (log) as `weight=1`, but adjust row indices if layout changes
- **Pattern**: `gui.py:66-79`
- **Depends on**: Task 1
- **Validate**: Visual — app starts with correct dark background

### Task 3: UPDATE `_create_widgets()` — Header Section in `gui.py`

- **Action**: UPDATE
- **Implement**: Replace header_frame + title_label with compact inline header:
  - Remove `self.header_frame` as a separate `CTkFrame`
  - Create `self.title_label` directly on `self` (the window), with:
    - `font=FONTS["title"]`
    - `text_color=COLORS["text_primary"]`
    - `text="TaxAct E-File Extension Bot"` (unchanged)
    - `anchor="w"` for left-alignment
  - A subtle separator line below (optional: thin `CTkFrame` with `height=1`, `fg_color=COLORS["border_subtle"]`)
- **Pattern**: `gui.py:83-89`
- **Depends on**: Task 1
- **Validate**: Visual — title appears top-left, compact

### Task 4: UPDATE `_create_widgets()` — Return Type Hero Card in `gui.py`

- **Action**: UPDATE
- **Implement**: Transform return_type_frame into a prominent Hero Card:
  - `self.return_type_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=COLORS["bg_card"], border_width=1, border_color=COLORS["border_subtle"])`
  - `self.return_type_label`: change text to `"SELECT RETURN TYPE"`, font=`FONTS["section"]`, text_color=`COLORS["text_secondary"]`, centered
  - `self.return_type_selector`: increase size and styling:
    - `height=42`
    - `font=ctk.CTkFont(family="Segoe UI Semibold", size=15)`
    - `selected_color=COLORS["accent"]`
    - `selected_hover_color=COLORS["accent_hover"]`
    - `unselected_color=COLORS["bg_input"]`
    - `unselected_hover_color="#3a3a3a"`
    - `text_color=COLORS["text_primary"]`
    - `corner_radius=8`
  - Keep: `values=["1120", "1120S", "1040"]`, `.set("1120S")`
- **CRITICAL**: `self.return_type_selector` attribute name unchanged — used in `_start_countdown` (Z.218), `_set_ready_state` (Z.271), `_start_bot` (Z.297)
- **Pattern**: `gui.py:92-103`
- **Depends on**: Task 1
- **Validate**: Visual — Return Type is the most prominent card

### Task 5: UPDATE `_create_widgets()` — Control Card in `gui.py`

- **Action**: UPDATE
- **Implement**: Style control_frame as Card:
  - `self.control_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=COLORS["bg_card"], border_width=1, border_color=COLORS["border_subtle"])`
  - `self.start_button`: update initial styling:
    - `fg_color=COLORS["success"]` (was `"green"`)
    - `hover_color=COLORS["success_hover"]` (was `"darkgreen"`)
    - `font=ctk.CTkFont(family="Segoe UI Semibold", size=15)` (was size=16)
    - `height=48` (was 50)
    - `corner_radius=8`
    - `command=self._on_start_click` (unchanged)
  - `self.countdown_label`: `font=ctk.CTkFont(family="Segoe UI", size=48, weight="bold")`, `text_color=COLORS["text_primary"]`
  - `self.countdown_hint`: `font=ctk.CTkFont(family="Segoe UI", size=14)`, `text_color=COLORS["text_secondary"]`
- **CRITICAL**: All 3 button states must be updated in their respective methods:
  - `_start_countdown()` Z.221-225: `fg_color=COLORS["warning"]`, `hover_color=COLORS["warning_hover"]`
  - `_set_ready_state()` Z.275-279: `fg_color=COLORS["success"]`, `hover_color=COLORS["success_hover"]`
  - `_set_running_state()` Z.287-291: `fg_color=COLORS["error"]`, `hover_color=COLORS["error_hover"]`
- **Pattern**: `gui.py:106-125`
- **Depends on**: Task 1
- **Validate**: Visual — button colors match design tokens in all 3 states

### Task 6: UPDATE `_create_widgets()` — Status Card in `gui.py`

- **Action**: UPDATE
- **Implement**: Style status_frame as Card:
  - `self.status_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=COLORS["bg_card"], border_width=1, border_color=COLORS["border_subtle"])`
  - `self.status_label`: `font=ctk.CTkFont(family="Segoe UI", size=13)`, `text_color=COLORS["text_primary"]`
  - `self.taxact_status_label`: `font=ctk.CTkFont(family="Segoe UI", size=12)` — keep dynamic `text_color` in `check_taxact_on_startup()`
  - `self.progress_label`: `font=ctk.CTkFont(family="Segoe UI", size=12)`, `text_color=COLORS["text_secondary"]`
- **CRITICAL**: `check_taxact_on_startup()` sets `text_color` to `"orange"`, `"green"`, `"red"` — these should be updated to use COLORS tokens: `COLORS["warning"]`, `COLORS["success"]`, `COLORS["error"]`
- **Pattern**: `gui.py:128-143`, `gui.py:385-411`
- **Depends on**: Task 1
- **Validate**: Visual — status card with correct colors for all 3 validation states

### Task 7: UPDATE `_create_widgets()` — Log Card in `gui.py`

- **Action**: UPDATE
- **Implement**: Style log_frame as Card:
  - `self.log_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=COLORS["bg_card"], border_width=1, border_color=COLORS["border_subtle"])`
  - `self.log_label`: `font=ctk.CTkFont(family="Segoe UI", size=12)`, `text_color=COLORS["text_secondary"]`
  - `self.log_textbox`:
    - `font=ctk.CTkFont(family="Consolas", size=12)` — Monospace
    - `fg_color=COLORS["bg_input"]` — darker than card
    - `text_color=COLORS["text_primary"]`
    - `corner_radius=6`
    - Keep: `height=200`, `state="disabled"`, `wrap="word"`
- **Pattern**: `gui.py:146-158`
- **Depends on**: Task 1
- **Validate**: Visual — log uses monospace font, darker background

### Task 8: UPDATE `_setup_layout()` in `gui.py`

- **Action**: UPDATE
- **Implement**: Adjust layout for new structure:
  - **Row 0 — Header**: `self.title_label.grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")` — compact, left-aligned, no frame
  - Optional: `self.separator.grid(row=1, ...)` if separator was added
  - **Row 1 (or 2) — Return Type Hero Card**: `self.return_type_frame.grid(row=1, column=0, padx=24, pady=(8, 6), sticky="ew")`
    - Inside: `self.return_type_label.pack(padx=16, pady=(14, 4), anchor="center")` — centered label
    - Inside: `self.return_type_selector.pack(padx=16, pady=(4, 14), fill="x")` — full width, centered
  - **Row 2 (or 3) — Control Card**: `self.control_frame.grid(row=2, column=0, padx=24, pady=6, sticky="ew")`
    - Inside: `self.start_button.pack(pady=16, padx=16, fill="x")`
  - **Row 3 (or 4) — Status Card**: `self.status_frame.grid(row=3, column=0, padx=24, pady=6, sticky="new")`
    - Inside: labels with `padx=16`, `anchor="w"`
  - **Row 4 (or 5) — Log Card**: `self.log_frame.grid(row=4, column=0, padx=24, pady=(6, 20), sticky="nsew")`
    - Inside: grid layout as before, `padx=12`
  - Update `self.grid_rowconfigure()` to keep log row expandable
- **CRITICAL**: Countdown labels (`countdown_label`, `countdown_hint`) are packed/unpacked dynamically inside `control_frame`. The `pack_forget()`/`pack()` sequence in `_start_countdown`, `_finish_countdown`, `_cancel_countdown`, `_set_ready_state` must match the new padding values.
- **Pattern**: `gui.py:160-187`
- **Depends on**: Tasks 3-7
- **Validate**: Visual — all cards visible, log expands vertically, spacing consistent

### Task 9: UPDATE State Machine Button Colors in `gui.py`

- **Action**: UPDATE
- **Implement**: Update hardcoded color strings in 3 methods:
  - `_start_countdown()` Z.221-225:
    - `fg_color="orange"` → `fg_color=COLORS["warning"]`
    - `hover_color="darkorange"` → `hover_color=COLORS["warning_hover"]`
  - `_set_ready_state()` Z.275-279:
    - `fg_color="green"` → `fg_color=COLORS["success"]`
    - `hover_color="darkgreen"` → `hover_color=COLORS["success_hover"]`
  - `_set_running_state()` Z.287-291:
    - `fg_color="red"` → `fg_color=COLORS["error"]`
    - `hover_color="darkred"` → `hover_color=COLORS["error_hover"]`
  - Update padding in `_start_countdown` pack calls to match Task 8 values
  - Update padding in `_set_ready_state` pack call to match Task 8 values
- **CRITICAL**: Do NOT change any logic, only color values and padding values.
- **Pattern**: `gui.py:212-291`
- **Depends on**: Task 1, Task 8
- **Validate**: Start app → click Start → verify Cancel is amber → cancel → verify Start is green again

### Task 10: UPDATE `check_taxact_on_startup()` Colors in `gui.py`

- **Action**: UPDATE
- **Implement**: Replace hardcoded color strings:
  - `text_color="orange"` → `text_color=COLORS["warning"]` (Z.391)
  - `text_color="green"` → `text_color=COLORS["success"]` (Z.403)
  - `text_color="red"` → `text_color=COLORS["error"]` (Z.409)
- **CRITICAL**: Do NOT change any logic or text content.
- **Pattern**: `gui.py:385-411`
- **Depends on**: Task 1
- **Validate**: Start app with `skip_taxact_validation=true` → verify orange text appears

### Task 11: UPDATE `config/settings.json` — GUI dimensions

- **Action**: UPDATE
- **Implement**: Adjust window dimensions if needed:
  - `window_height`: `650` → may need `680` for additional card padding (verify visually)
  - Keep `window_width: 500`
  - Keep all other settings unchanged
- **Depends on**: Tasks 1-10
- **Validate**: Start app → all content visible without scrolling, log area has reasonable height

## Testing Requirements

No automated tests needed — this is a purely visual change. The existing state machine logic is untouched.

- [ ] **Visual**: App starts with dark background (#1a1a1a), cards visible (#242424)
- [ ] **Visual**: Return Type is the most prominent card, centered selector, full width
- [ ] **Visual**: Fonts are Segoe UI, log is Consolas monospace
- [ ] **Functional**: Return Type selector works — click 1120, 1120S, 1040
- [ ] **Functional**: Start → Countdown (5-4-3-2-1) → Cancel works
- [ ] **Functional**: Start → Countdown → Running → Stop works
- [ ] **Functional**: TaxAct validation status shows correct color (orange for dev skip)
- [ ] **Functional**: Log messages appear and scroll to bottom
- [ ] **Functional**: Window close while running stops bot cleanly
- [ ] **Functional**: `return_type_selector.get()` returns correct value after redesign
- [ ] Edge case: Resize window — log card should expand, other cards stay fixed

**Test Levels**: Manual E2E only (no unit tests — no logic changes)

## Bug Handling

During implementation:
- Bugs caused by THESE changes → Fix immediately
- Pre-existing bugs discovered → Document in `.agents/bugs/`, do NOT fix
- NEVER modify working code outside the scope of this plan

## Rollback Strategy

If implementation fails:
1. `git checkout -- clickbot/gui.py config/settings.json` to revert all changes
2. No other files are affected

## Manual Verification

After implementation, manually verify:
- [ ] `python -m clickbot.gui` starts without errors
- [ ] All 5 sections visible (Header, Return Type, Control, Status, Log)
- [ ] Return Type selector is visually the most prominent element
- [ ] Click through all 3 GUI states: Ready → Countdown → Cancel → Ready
- [ ] Log entries appear with monospace font
- [ ] Window resize: log expands, cards stay fixed
- [ ] Compare before/after screenshot

## Notes

- **Font Fallback**: "Segoe UI Semibold" is available on Windows 10/11. If it fails, CustomTkinter falls back to Roboto gracefully.
- **Consolas Fallback**: Available on all Windows versions since Vista. Safe choice.
- **No custom theme JSON needed** — all colors are applied directly via widget parameters, avoiding dependency on external theme files.
- The `header_frame` widget is removed in favor of a direct label on the window. If any future code references `self.header_frame`, it would break — but the audit confirmed nothing external references it.
- The `pack_forget()`/`pack()` sequences in the countdown flow are the highest-risk area. Padding values must be consistent between `_start_countdown`, `_finish_countdown`, `_cancel_countdown`, and `_set_ready_state`.
