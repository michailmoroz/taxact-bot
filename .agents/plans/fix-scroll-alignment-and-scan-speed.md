# Plan: Fix Scroll Alignment & Scan Speed

## User Story

Als Steuerberater möchte ich, dass der Bot nach dem Scrollen in der Client-Tabelle
weiterhin Clients mit leerem Fed EF Status erkennt und die Tabelle schneller scannt,
damit der Loop-Modus zuverlässig alle Clients bearbeitet.

## Acceptance Criteria

- [ ] Nach Scroll bleiben Zeilen korrekt aligned (kein Anschneiden der ersten Zeile)
- [ ] Bot erkennt Clients mit leerem Fed EF Status auch nach mehrfachem Scroll
- [ ] Tabellen-Scan ist spürbar schneller (Fed EF Status wird zuerst geprüft)
- [ ] Bestehende Funktionalität (erster Scan ohne Scroll) bleibt unverändert

## Context

Der Bot scrollt in der Client-Tabelle mit `scroll(-300)`, was 300px entspricht.
Bei 32px Zeilenhöhe sind das 9.375 Zeilen — die erste Zeile wird angeschnitten.
Dadurch liegt das feste OCR-Raster (y=202, 234, 266...) nicht mehr auf den Zeilen,
und alle OCR-Reads liefern Müll. Fix: `amount` auf `-320` (exakt 10 Zeilen).

Zusätzlich liest `scan_table_row()` immer alle 3 Spalten per OCR, auch wenn
`fed_ef_status` allein reichen würde um die Zeile zu überspringen. Fix: Status
zuerst lesen, bei Non-Empty sofort skippen.

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `config/settings.json` | Scroll amount `-300` | L70 |
| `clickbot/vision.py` | `scan_table_row()` — liest alle 3 Spalten | L668-724 |
| `clickbot/vision.py` | `_scan_visible_clients()` — Scan-Loop | L727-797 |
| `clickbot/vision.py` | `find_next_client()` — Scroll-Loop | L800-873 |

### Patterns to Follow
- `read_cell()` inner function in `scan_table_row()` (vision.py:693) für Spalten-OCR
- `_scan_visible_clients()` prüft `is_status_empty` erst nach vollständigem Row-Scan (vision.py:772)

## Dependencies

- **New Packages**: none
- **Affected Modules**: `clickbot/vision.py`, `config/settings.json`
- **Breaking Changes**: No

## Tasks

### Task 1: UPDATE `config/settings.json`

- **Action**: UPDATE
- **Implement**: Ändere `loop.scroll_in_table.amount` von `-300` auf `-320` (exakt 10 Zeilen à 32px)
- **Depends on**: none
- **Validate**: `grep "amount" config/settings.json` → should show `-320`

### Task 2: UPDATE `clickbot/vision.py` — Fed EF Status zuerst lesen

- **Action**: UPDATE
- **Implement**: In `_scan_visible_clients()` (L755-797), statt `scan_table_row()` aufzurufen
  (das alle 3 Spalten liest), die Logik umstrukturieren:
  1. Zuerst NUR `fed_ef_status` per OCR lesen (via `read_cell` Logik)
  2. Wenn Status non-empty → sofort `continue` (skip row, nur 1 OCR call statt 3)
  3. Wenn Status empty → dann `client_name` und `return_type` lesen
  4. Weiter mit bestehender Filterlogik

  Konkret: Eine neue Hilfsfunktion `_read_single_cell()` extrahieren aus der
  `read_cell()` inner function in `scan_table_row()` (vision.py:693-710),
  die eine einzelne Spalte an einer gegebenen Y-Position liest.
  Dann in `_scan_visible_clients()` nutzen für den Fast-Path.

  Der bestehende `scan_table_row()` bleibt unverändert (wird ggf. anderswo gebraucht).

- **Pattern**: `read_cell()` in `scan_table_row()` (vision.py:693-710)
- **Depends on**: none
- **Validate**: `python -m pytest tests/ -v` — alle bestehenden Tests müssen passen

### Task 3: UPDATE `clickbot/vision.py` — Empty-row Detection anpassen

- **Action**: UPDATE
- **Implement**: In der neuen Logik aus Task 2 muss die Empty-Row-Detection
  (aktuell L760: `if not row_data.client_name: break`) angepasst werden.
  Statt auf leeren client_name zu prüfen (der jetzt erst nach dem Status-Check
  gelesen wird), eine der folgenden Strategien verwenden:
  - `client_name` lesen und bei leerem Namen `break` (wie bisher, aber nur
    wenn auch Status leer ist — d.h. bei leerem Status + leerem Namen = Tabellenende)
  - Oder: Alle max_rows durchiterieren ohne Early-Break auf leere Zeilen,
    da nach dem Scroll leere Zeilen in der Mitte auftreten können

  Empfehlung: `client_name` immer lesen (wird eh gebraucht für processed-Check
  und Logging), nur `return_type` erst lesen wenn Status leer ist.
  Reihenfolge pro Zeile:
  1. `fed_ef_status` lesen → non-empty? → skip (1 OCR call)
  2. `client_name` lesen → empty? → break (2 OCR calls, Tabellenende)
  3. `client_name` in processed? → skip (2 OCR calls)
  4. `return_type` lesen → vollständiger ClientRow (3 OCR calls, nur für Kandidaten)

- **Depends on**: Task 2
- **Validate**: `python -m pytest tests/ -v`

## Testing Requirements

- [ ] Unit Test: `_read_single_cell()` liest korrekte Spalte an gegebener Y-Position
- [ ] Unit Test: `_scan_visible_clients()` skippt Zeilen mit non-empty Status nach 1 OCR call
- [ ] Manueller E2E-Test: Bot scrollt in Client-Tabelle und findet Clients nach Scroll

**Test Levels**: Unit + E2E (manuell)

## Bug Handling

- Bugs durch DIESE Änderungen → sofort fixen
- Vorbestehende Bugs → in `.agents/bugs/` dokumentieren, NICHT fixen
- KEIN Code außerhalb des Scopes ändern

## Rollback Strategy

1. `git stash` oder `git checkout .` um Änderungen rückgängig zu machen
2. Scroll amount in settings.json zurück auf `-300`

## Manual Verification

Nach Implementation auf dem Remote-PC testen:
- [ ] Bot startet, scannt erste Seite der Client-Tabelle
- [ ] Bot scrollt und erkennt Clients mit leerem Fed EF Status nach Scroll
- [ ] Erste Zeile nach Scroll ist NICHT angeschnitten
- [ ] Scan ist merkbar schneller (weniger OCR-Aufrufe im Log sichtbar)
- [ ] Bot bearbeitet mindestens 3 Clients über Scroll-Grenzen hinweg

## Notes

- Scroll-Messung ergab: 1 Pixel pro `scroll(-1)` Notch in TaxAct
- `-320` = exakt 10 Zeilen à 32px = sauberes Alignment
- Die Speed-Optimierung spart 2 von 3 OCR-Calls pro Zeile mit non-empty Status
  (bei 20 sichtbaren Zeilen mit 18 bereits bearbeiteten: 36 OCR-Calls gespart)
