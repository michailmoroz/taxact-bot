# Plan: GUI Redesign — Layout & Visuelle Hierarchie

## User Story

Als Steuerberater moechte ich eine uebersichtlichere GUI mit prominenter CSV-Anzeige und klarer Aktions-Hierarchie, damit ich auf einen Blick sehe welche Datei geladen ist, wie viele Clients offen sind, und schnell den Bot starten kann.

## Acceptance Criteria

- [ ] CSV-Dateiname ist das prominenteste Element (gross, bold, ganz oben)
- [ ] Browse-Button ist sichtbar und nicht versteckt
- [ ] Stat-Badges (TODO/Done/FAIL) sind farbig und nebeneinander
- [ ] Return Type + Start Bot sind in einer Card zusammengefasst
- [ ] Scan Client Table ist visuell kleiner/sekundaer (Outline-Style)
- [ ] TaxAct-Info steht inline unter dem Titel
- [ ] Status-Card ist kompakt (eine Zeile)
- [ ] Fenster ist groesser (breiter + hoeher)
- [ ] Alle bestehenden Funktionen (Countdown, Preprocessing, State-Machine) bleiben intakt
- [ ] Bestehende Farben (Design Tokens) bleiben unveraendert

## Context

Die aktuelle GUI hat eine falsche visuelle Hierarchie: "Scan Client Table" dominiert, die CSV-Datei ist versteckt, und es gibt zu viele gleichwertige Cards. Das Redesign verschiebt die CSV-Datei nach oben als prominentestes Element, fasst Return Type + Start Bot zusammen, und stuft den Scan-Button herab. Nur `gui.py` und `settings.json` werden geaendert — keine Logik-Aenderungen.

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `clickbot/gui.py` | Gesamte GUI — Widgets, Layout, State-Machine | 893 Zeilen, alles relevant |
| `config/settings.json` | `gui.window_width/height` | Zeilen 42-48 |
| `.agents/notizen/GUI-new-vs-old.md` | Design-Referenz mit ASCII-Mockups | Gesamtes Dokument |

### Patterns to Follow
- Widget-Erstellung in `_create_widgets()` (`gui.py:133-331`)
- Layout via `_setup_layout()` (`gui.py:333-381`)
- State-Machine Methoden (`_set_ready_state`, `_start_countdown`, etc.) verwenden `pack_forget()` + `pack()` fuer dynamisches Ein-/Ausblenden
- Preprocessing-Countdown nutzt gleichen Pattern wie Bot-Countdown

### Keine GUI-Tests vorhanden
Es gibt keine Unit-Tests fuer `gui.py`. Die State-Machine-Logik wird nur manuell getestet.

## Dependencies

- **New Packages**: none
- **Affected Modules**: `clickbot/gui.py`, `config/settings.json`
- **Breaking Changes**: Nein — nur visuelle Aenderungen, keine API/Logik-Aenderungen

## Tasks

### Task 1: UPDATE `config/settings.json` — Fenstergroesse erhoehen

- **Action**: UPDATE
- **Implement**: `window_width` von 500 auf 580, `window_height` von 820 auf 900 aendern
- **Pattern**: Bestehende Werte in `settings.json:43-44`
- **Depends on**: none
- **Validate**: `python -c "import json; d=json.load(open('config/settings.json')); assert d['gui']['window_width']==580 and d['gui']['window_height']==900"`

### Task 2: UPDATE `gui.py` — FONTS erweitern

- **Action**: UPDATE
- **Implement**: Neue Font-Eintraege im `FONTS` dict hinzufuegen:
  - `"file_name": ("Segoe UI Semibold", 15)` — fuer den grossen CSV-Dateinamen
  - `"file_path": ("Segoe UI", 11)` — fuer den Verzeichnispfad
  - `"stat_number": ("Segoe UI Semibold", 20)` — fuer die grossen Zahlen in Stat-Badges
  - `"stat_label": ("Segoe UI", 11)` — fuer die Labels unter den Zahlen
  - `"section_label": ("Segoe UI", 11)` — fuer Muted Section-Labels ("CLIENT FILE", "RETURN TYPE")
  - `"taxact_inline": ("Segoe UI", 12)` — fuer TaxAct-Info unter Titel
- **Pattern**: Bestehende FONTS in `gui.py:51-60`
- **Depends on**: none
- **Validate**: `grep -c "file_name\|stat_number\|section_label" clickbot/gui.py` (sollte >= 3 sein)

### Task 3: UPDATE `gui.py` — `_setup_window()` anpassen

- **Action**: UPDATE
- **Implement**: `minsize` von `(420, 680)` auf `(500, 750)` aendern. `grid_rowconfigure` fuer neues Row-Layout anpassen:
  - Row 0: Titel + TaxAct-Info (weight=0)
  - Row 1: Client File Card (weight=0)
  - Row 2: Controls Card (weight=0)
  - Row 3: Preprocessing Card (weight=0)
  - Row 4: Status-Zeile (weight=0)
  - Row 5: Log Card (weight=1, expandiert)
- **Pattern**: `gui.py:114-131`
- **Depends on**: Task 1
- **Validate**: `grep "minsize" clickbot/gui.py` (sollte 500, 750 zeigen)

### Task 4: UPDATE `gui.py` — `_create_widgets()` komplett umbauen

- **Action**: UPDATE
- **Implement**: Die gesamte `_create_widgets()` Methode umstrukturieren. Bestehende Widgets werden neu angeordnet und einige neue hinzugefuegt:

  **Header (Row 0) — kein Frame, direkt auf self:**
  - `self.title_label` — bleibt (Text, Font unveraendert)
  - `self.taxact_status_label` — NEU: Wird direkt unter Titel platziert statt in Status-Card. Font: `taxact_inline`, initial `"TaxAct: Checking..."`

  **Client File Card (Row 1) — NEUE prominente Card:**
  - `self.client_file_frame` — Neuer CTkFrame (ersetzt den alten `preprocessing_frame` als Container fuer CSV-Info)
  - `self.client_file_section_label` — NEU: CTkLabel "CLIENT FILE", Font: `section_label`, Farbe: `text_muted`
  - `self.csv_name_row` — NEU: CTkFrame (transparent) fuer Dateiname + Browse nebeneinander
  - `self.csv_path_label` — BESTEHEND, aber: Font von `caption` auf `file_name` aendern, Text-Farbe auf `text_primary`
  - `self.csv_browse_button` — BESTEHEND, aber: Groesser machen (height=32, width=80)
  - `self.csv_dir_label` — NEU: CTkLabel fuer Verzeichnispfad, Font: `file_path`, Farbe: `text_muted`
  - `self.stats_row` — NEU: CTkFrame (transparent) fuer 3 Stat-Badges nebeneinander
  - 3x Stat-Badge Frames (jeweils CTkFrame mit Hintergrundfarbe + 2 Labels):
    - `self.stat_todo_frame`, `self.stat_todo_number`, `self.stat_todo_label`
    - `self.stat_done_frame`, `self.stat_done_number`, `self.stat_done_label`
    - `self.stat_fail_frame`, `self.stat_fail_number`, `self.stat_fail_label`
  - Badge-Farben:
    - TODO: bg=`#1e3a5f`, Zahl=`#60a5fa`, Label=`#999999`
    - Done: bg=`#14532d`, Zahl=`#4ade80`, Label=`#999999`
    - FAIL: bg=`#7f1d1d`, Zahl=`#f87171`, Label=`#999999`
  - Badge-Layout: corner_radius=8, Zahl oben (Font: `stat_number`), Label unten (Font: `stat_label`)

  **Controls Card (Row 2) — Return Type + Start Bot zusammen:**
  - `self.controls_frame` — Neuer CTkFrame (ersetzt separate `return_type_frame` + `control_frame`)
  - `self.return_type_label` — BESTEHEND, Text aendern auf "RETURN TYPE", Font auf `section_label`, Farbe auf `text_muted`, anchor=`"w"` statt `"center"`
  - `self.return_type_selector` — BESTEHEND, unveraendert
  - `self.start_button` — BESTEHEND, height von 48 auf 52 aendern
  - `self.countdown_label` — BESTEHEND, parent aendern auf `controls_frame`
  - `self.countdown_hint` — BESTEHEND, parent aendern auf `controls_frame`

  **Preprocessing Card (Row 3) — Herabgestuft:**
  - `self.preprocessing_frame` — BESTEHEND, bleibt als Frame
  - `self.preprocessing_button` — BESTEHEND, aber Outline-Style: `fg_color="transparent"`, `border_width=2`, `border_color=COLORS["accent"]`, `text_color=COLORS["accent"]`, height von 48 auf 36
  - `self.preproc_countdown_label` — BESTEHEND, parent bleibt `preprocessing_frame`
  - `self.preproc_countdown_hint` — BESTEHEND, parent bleibt `preprocessing_frame`

  **Status-Zeile (Row 4) — Kompakt:**
  - `self.status_frame` — BESTEHEND, wird kompakter
  - `self.status_label` — BESTEHEND, unveraendert
  - `self.progress_label` — BESTEHEND, auf gleicher Zeile wie status_label oder direkt darunter
  - `self.taxact_status_label` — ENTFERNT aus dieser Card (wandert nach Header)

  **Log Card (Row 5) — Unveraendert:**
  - `self.log_frame`, `self.log_label`, `self.log_textbox` — BESTEHEND, keine Aenderungen

  **Geloeschte Widgets:**
  - `self.csv_status_label` — Wird ersetzt durch die 3 Stat-Badges
  - `self.csv_file_frame` — Wird ersetzt durch `csv_name_row` in `client_file_frame`
  - `self.return_type_frame` — Wird in `controls_frame` zusammengefasst
  - `self.control_frame` — Wird in `controls_frame` zusammengefasst

- **Pattern**: `gui.py:133-331`
- **Depends on**: Task 2
- **Validate**: App startet ohne Fehler: `python -c "from clickbot.gui import BotGUI; print('import ok')"`

### Task 5: UPDATE `gui.py` — `_setup_layout()` komplett umbauen

- **Action**: UPDATE
- **Implement**: Neues Grid-Layout:

  ```
  pad_x = 24

  # Row 0 — Header
  self.title_label.grid(row=0, column=0, padx=pad_x, pady=(20, 0), sticky="w")
  self.taxact_status_label.grid(row=1, column=0, padx=pad_x, pady=(2, 8), sticky="w")

  # Row 1 — Client File Card (PROMINENT)
  self.client_file_frame.grid(row=2, column=0, padx=pad_x, pady=(4, 8), sticky="ew")
  # Intern: section_label, csv_name_row (path_label + browse), csv_dir_label, stats_row

  # Row 2 — Controls Card (Return Type + Start)
  self.controls_frame.grid(row=3, column=0, padx=pad_x, pady=6, sticky="ew")
  # Intern: return_type_label, return_type_selector, start_button

  # Row 3 — Preprocessing
  self.preprocessing_frame.grid(row=4, column=0, padx=pad_x, pady=6, sticky="ew")
  # Intern: preprocessing_button (outline)

  # Row 4 — Status (kompakt)
  self.status_frame.grid(row=5, column=0, padx=pad_x, pady=6, sticky="ew")
  # Intern: status_label, progress_label

  # Row 5 — Log (expandiert)
  self.log_frame.grid(row=6, column=0, padx=pad_x, pady=(6, 20), sticky="nsew")
  ```

  Row-Weights: Nur Row 6 bekommt weight=1 (Log expandiert). grid_rowconfigure muss in `_setup_window()` auf row=6 zeigen.

  **Interne Layouts der Cards:**

  Client File Card:
  ```
  section_label.pack(padx=16, pady=(12, 4), anchor="w")
  csv_name_row.pack(padx=16, fill="x")
    csv_path_label.pack(side="left", expand=True, fill="x")
    csv_browse_button.pack(side="right", padx=(8, 0))
  csv_dir_label.pack(padx=16, pady=(2, 8), anchor="w")
  stats_row.pack(padx=16, pady=(0, 14), fill="x")
    stat_todo_frame.pack(side="left", expand=True, fill="x", padx=(0, 4))
    stat_done_frame.pack(side="left", expand=True, fill="x", padx=4)
    stat_fail_frame.pack(side="left", expand=True, fill="x", padx=(4, 0))
  ```

  Controls Card:
  ```
  return_type_label.pack(padx=16, pady=(14, 4), anchor="w")
  return_type_selector.pack(padx=16, pady=(4, 10), fill="x")
  start_button.pack(padx=16, pady=(4, 16), fill="x")
  ```

  Preprocessing Card:
  ```
  preprocessing_button.pack(pady=12, padx=16, fill="x")
  ```

  Status Card:
  ```
  status_label.pack(anchor="w", padx=16, pady=(10, 4))
  progress_label.pack(anchor="w", padx=16, pady=(0, 10))
  ```

- **Pattern**: `gui.py:333-381`
- **Depends on**: Task 3, Task 4
- **Validate**: App startet und Layout ist korrekt sichtbar

### Task 6: UPDATE `gui.py` — `_load_csv_file()` fuer neue Widgets anpassen

- **Action**: UPDATE
- **Implement**: In `_load_csv_file()` (Zeile 570-605):
  - `csv_path_label` zeigt nur den Dateinamen (ohne `.../"` Prefix): `csv_path.name`
  - `csv_dir_label` zeigt den Verzeichnispfad: `str(csv_path.parent)`
  - Stat-Badges aktualisieren statt `csv_status_label`:
    - `self.stat_todo_number.configure(text=str(todo))`
    - `self.stat_done_number.configure(text=str(done))`
    - `self.stat_fail_number.configure(text=str(fail))`
  - Bei fehlender CSV (`_on_start_click` Fehlerfall, Zeile 631):
    - `csv_path_label.configure(text="No CSV loaded")`
    - `csv_dir_label.configure(text="")`
    - Alle Stat-Badge Zahlen auf "—" setzen
- **Pattern**: `gui.py:570-605`, `gui.py:624-633`
- **Depends on**: Task 4
- **Validate**: CSV laden und pruefen ob Dateiname gross und Counts in Badges angezeigt werden

### Task 7: UPDATE `gui.py` — State-Machine Methoden anpassen

- **Action**: UPDATE
- **Implement**: Alle Methoden die Widgets referenzieren muessen auf neue Namen/Parents aktualisiert werden:

  **`_set_ready_state()` (Zeile 691-719):**
  - `self.preprocessing_button.configure(state="normal")` bleibt
  - Button-Reset: `fg_color="transparent"`, `border_width=2`, `border_color=COLORS["accent"]`, `text_color=COLORS["accent"]` (Outline-Style)
  - `self.csv_browse_button.configure(state="normal")` bleibt

  **`_start_countdown()` (Zeile 640-664):**
  - Countdown-Labels in `controls_frame` statt `control_frame`
  - `pack_forget/pack` Reihenfolge anpassen an neues Layout (start_button ist in controls_frame nach return_type_selector)

  **`_finish_countdown()` (Zeile 684-689):**
  - Countdown-Labels `pack_forget()` — Widget-Referenzen bleiben gleich

  **`_start_preprocessing_countdown()` (Zeile 406-432):**
  - Countdown in `preprocessing_frame` — bleibt gleich
  - `preprocessing_button` Reset: Outline-Style statt filled

  **`_reset_preprocessing_button()` (Zeile 543-554):**
  - Button zurueck auf Outline-Style: `fg_color="transparent"`, `border_width=2`, `border_color=COLORS["accent"]`, `text_color=COLORS["accent"]`
  - Pack-Parameter anpassen: `pady=12` statt `(16, 8)`

  **`_finish_preprocessing_countdown()` (Zeile 453-484):**
  - Stop-Button: `fg_color=COLORS["error"]` (filled, nicht outline) — waehrend Scan bleibt der Button filled

  **`check_taxact_on_startup()` (Zeile 833-859):**
  - `taxact_status_label` ist jetzt direkt unter dem Titel (nicht in status_frame) — configure-Aufrufe bleiben gleich, nur Position aendert sich

- **Pattern**: `gui.py:406-719`
- **Depends on**: Task 4, Task 5
- **Validate**: Bot starten → Countdown → Cancel → Ready-State korrekt wiederhergestellt

### Task 8: UPDATE `gui.py` — Preprocessing-Countdown in neuem Layout

- **Action**: UPDATE
- **Implement**: Die `preproc_countdown_label` und `preproc_countdown_hint` werden weiterhin in `preprocessing_frame` angezeigt. Da die Card jetzt kleiner ist, muessen die Countdown-Elemente die Card temporaer vergroessern:
  - `_start_preprocessing_countdown()`: Button auf filled-Warning umschalten (wie bisher), Countdown-Labels einblenden
  - `_finish_preprocessing_countdown()`: Button auf filled-Error "Stop Scan" umschalten
  - `_reset_preprocessing_button()`: Zurueck auf Outline-Style
  - Gleiche pack_forget/pack Logik wie bisher, nur mit neuen Button-Styles
- **Pattern**: `gui.py:406-554`
- **Depends on**: Task 7
- **Validate**: Preprocessing starten → Countdown sichtbar → Stop → Button zurueck auf Outline

## Testing Requirements

Keine automatisierten GUI-Tests vorhanden. Alle Validierung ist manuell.

- [ ] App startet ohne Fehler
- [ ] CSV wird beim Start automatisch geladen (falls vorhanden)
- [ ] Dateiname prominent angezeigt, Verzeichnispfad klein darunter
- [ ] Stat-Badges zeigen korrekte Zahlen mit Farben
- [ ] Browse-Button oeffnet File-Dialog und aktualisiert alle Felder
- [ ] Return Type Selector funktioniert
- [ ] Start Bot → Countdown → Bot laeuft → Stop funktioniert
- [ ] Scan Client Table → Preprocessing-Countdown → Scan → Stop funktioniert
- [ ] Fenstergröße ist groesser als vorher
- [ ] Edge case: Kein CSV geladen → Start Bot disabled, Stat-Badges zeigen "—"

**Test Levels**: Manuell (E2E)

## Bug Handling

- Bugs durch DIESE Aenderungen → Sofort fixen
- Vorher existierende Bugs → Dokumentieren in `.agents/bugs/`, NICHT fixen
- NIEMALS funktionierenden Code ausserhalb des Scopes aendern

## Rollback Strategy

1. `git checkout -- clickbot/gui.py config/settings.json` zum Zuruecksetzen
2. Keine weiteren Dateien betroffen

## Manual Verification

- [ ] App starten: Alle Cards in korrekter Reihenfolge (Client File → Controls → Scan → Status → Log)
- [ ] CSV laden via Browse: Dateiname gross, Pfad klein, Badges farbig
- [ ] Start Bot: Countdown in Controls-Card, kein visueller Glitch
- [ ] Preprocessing: Countdown in Preprocessing-Card, Button wechselt Outline → Warning → Error → Outline
- [ ] Fenster vergroessern/verkleinern: Layout bleibt konsistent, Log expandiert
- [ ] TaxAct-Info unter Titel sichtbar (gruen/rot/gelb je nach Status)

## Notes

- Die Logik (State-Machine, BotController-Integration, Preprocessing-Thread) bleibt komplett unveraendert
- Nur Widget-Erstellung, Layout-Anordnung und visuelle Eigenschaften werden geaendert
- `_on_close()` braucht keine Aenderung — referenziert nur `controller` und `_preprocessing_stop`
- Die `main()` Funktion am Ende bleibt unveraendert
- Countdown-Logik fuer Bot und Preprocessing nutzt denselben Pattern — beide muessen konsistent angepasst werden

## Confidence Score: 8/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 9 | Klare Widget/Layout-Trennung, gut strukturierter Code |
| **External Knowledge** | 9 | CustomTkinter ist gut dokumentiert, keine neuen APIs noetig |
| **Risk** | 7 | State-Machine hat viele pack_forget/pack Aufrufe die konsistent bleiben muessen |
| **Dependencies** | 9 | Nur 2 Dateien betroffen, keine Cascade-Effekte |
| **Clarity** | 8 | Design-Mockup liegt vor, User hat alle Fragen beantwortet |
| **Testability** | 6 | Keine automatisierten GUI-Tests, nur manuelle Verifikation moeglich |

**Overall: 8/10** — Rein visuelles Refactoring einer einzelnen Datei mit klarem Mockup. Hauptrisiko sind die vielen pack_forget/pack State-Transitions die alle konsistent angepasst werden muessen.
