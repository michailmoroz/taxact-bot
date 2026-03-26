# Plan: SSN/EIN OCR-Verbesserung & ID-Only Matching

## User Story

Als Steuerberater moechte ich, dass der Bot die SSN/EIN-Nummern zuverlaessig erkennt und Clients nur anhand der ID (SSN/EIN) abgleicht, damit keine Clients uebersprungen werden wegen falscher OCR-Erkennung.

## Acceptance Criteria

- [ ] SSN/EIN-OCR verwendet 3x Upscaling, Digit-Whitelist und PSM 7
- [ ] CSV-Matching verwendet NUR client_id (SSN/EIN) — kein client_name, kein return_type
- [ ] `normalize_ssn_ein()` setzt bei 8 Digits nicht mehr blind eine 0 voran
- [ ] `debug_ocr.py` verwendet dieselbe verbesserte OCR-Pipeline fuer SSN/EIN
- [ ] Alle bestehenden Tests laufen (angepasst an neue Matching-Logik)

## Context

Der Bot uebersieht bei der OCR-Erkennung regelmaessig einzelne Ziffern in SSN/EIN-Nummern (nicht nur fuehrende Nullen, sondern auch 2. oder 3. Ziffer). Dadurch wird die SSN/EIN falsch gelesen, der Safeguard haengt blind eine 0 vorn an, die resultierende ID existiert nicht in der CSV und der Client wird uebersprungen. Die Loesung hat zwei Teile: (1) OCR-Qualitaet fuer Ziffern massiv verbessern, (2) Matching vereinfachen auf nur SSN/EIN.

## Research Summary

### Relevant Files
| File | Purpose | Lines |
|------|---------|-------|
| `clickbot/vision.py` | OCR-Pipeline + Matching-Logik | 679-702 (normalize), 859-930 (preprocessing scan), 933-1080 (CSV scan), 1083-1214 (legacy scan) |
| `clickbot/preprocessor.py` | CSV update matching | 287-298 (update_client_status) |
| `debug_ocr.py` | Debug-Visualisierung | 90-95 (OCR per Zelle) |
| `tests/unit/test_csv_integration.py` | CSV-Matching Tests | 84-275 (scan tests), 429-637 (CSV scan tests) |
| `tests/unit/test_1120_process.py` | normalize_ssn_ein Tests | 323-365 |

### Patterns to Follow
- OCR in `vision.py:905-909` und `vision.py:991-995`: `crop → RGB→GRAY → pytesseract.image_to_string()`
- Gleiche Pipeline in `debug_ocr.py:90-95`
- Matching Keys in `vision.py:969-981` und `vision.py:1125-1132`

## Dependencies

- **New Packages**: none
- **Affected Modules**: `vision.py`, `preprocessor.py`, `debug_ocr.py`, `test_csv_integration.py`, `test_1120_process.py`
- **Breaking Changes**: Ja — Matching-Keys aendern sich von Composite auf ID-only. Alle Tests mit Key-Assertions muessen angepasst werden. Backward-Compat fuer In-Memory-Modus (ohne CSV) bleibt unveraendert.

## Tasks

### Task 1: ADD `_ocr_digits()` Helper in `vision.py`

- **Action**: ADD
- **Implement**: Neue Funktion `_ocr_digits(pil_image: Image.Image) -> str` die:
  1. PIL Image (Grayscale) empfaengt
  2. 3x Upscale via `cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)`
  3. `pytesseract.image_to_string()` mit Config `--psm 7 -c tessedit_char_whitelist=0123456789-`
  4. Ergebnis stripped und erste Zeile zurueckgibt
- **Position**: Nach `read_text_region()` (nach Zeile 445), vor den Client-Table-Funktionen
- **Pattern**: Aehnlich wie `read_text_region()` (vision.py:404-445), aber spezialisiert
- **Depends on**: none
- **Validate**: `pytest tests/unit/test_1120_process.py -v -k "ssn"` (nach Task 7)

### Task 2: UPDATE `scan_visible_clients_csv()` — OCR fuer SSN/EIN

- **Action**: UPDATE
- **Implement**: In `_crop_and_ocr()` (vision.py:983-998) eine Unterscheidung einfuegen:
  - Wenn `col_name == "ssn_ein"`: nach Grayscale-Konvertierung `_ocr_digits(region_pil)` aufrufen statt `pytesseract.image_to_string(region_pil, lang="eng")`
  - Alle anderen Spalten: unveraendert
- **Depends on**: Task 1
- **Validate**: Manuell mit `debug_ocr.py` oder Bot-Run

### Task 3: UPDATE `read_all_rows_from_screenshot()` — OCR fuer SSN/EIN

- **Action**: UPDATE
- **Implement**: In der Schleife (vision.py:896-912) nach Grayscale-Konvertierung:
  - Wenn `col_name == "ssn_ein"`: `_ocr_digits(region_pil)` aufrufen
  - Sonst: bestehenden `pytesseract.image_to_string()` Aufruf beibehalten
- **Depends on**: Task 1
- **Validate**: Manuell mit Preprocessing-Scan

### Task 4: UPDATE `_read_single_cell()` — OCR fuer SSN/EIN

- **Action**: UPDATE
- **Implement**: Parameter `col_name` wird bereits uebergeben (vision.py:821). Nach `read_text_region()` Aufruf (Zeile 854) eine Sonderbehandlung:
  - Wenn `col_name == "ssn_ein"`: Stattdessen direkt crop + grayscale + `_ocr_digits()` verwenden (wie in `_crop_and_ocr`)
  - ODER: `read_text_region()` um optionalen Parameter `digit_mode=False` erweitern und bei True `_ocr_digits()` nutzen
  - Einfacher: In `_read_single_cell()` den OCR-Aufruf inline duplizieren fuer SSN/EIN (analog zu `_crop_and_ocr`)
- **Depends on**: Task 1
- **Validate**: `pytest tests/unit/ -v`

### Task 5: UPDATE `normalize_ssn_ein()` — Safeguard entfernen

- **Action**: UPDATE
- **Implement**: In `vision.py:694-695`:
  - Zeile `if len(digits) == 8: digits = "0" + digits` **entfernen**
  - Stattdessen: Wenn `len(digits) != 9` → `return raw_value` (bereits vorhanden auf Zeile 696-697, wird jetzt auch fuer 8-Digit-Werte greifen)
  - Kommentar hinzufuegen: `# 8-digit values are NOT padded — OCR improvement should prevent this`
- **Depends on**: none
- **Validate**: `pytest tests/unit/test_1120_process.py -v -k "normalize_ssn_ein"`

### Task 6: UPDATE Matching-Logik — ID-only fuer alle Return Types

- **Action**: UPDATE
- **Implement**: An 6 Stellen die Keys vereinfachen:

  **6a) `scan_visible_clients_csv()` (vision.py:965-981)**:
  - `use_id_only` Variable und if/else entfernen
  - Key wird immer: `key = (csv_id,)` (Tuple mit einem Element)
  - `csv_keys` und `skip_keys` verwenden nur `(csv_id,)`

  **6b) `scan_visible_clients_csv()` (vision.py:1034-1038)**:
  - Key wird immer: `key = (ssn_ein,)`

  **6c) `_scan_visible_clients()` (vision.py:1125-1132)**:
  - `key = (r.client_id,)` statt `(r.client_name, r.client_id, r.return_type)`
  - `csv_lookup` Keys ebenfalls anpassen

  **6d) `_scan_visible_clients()` (vision.py:1152)**:
  - `csv_key = (ssn_ein,)` statt `(client_name, ssn_ein, selected_return_type)`

  **6e) `_scan_visible_clients()` (vision.py:1179)**:
  - `if (ssn_ein,) in skip_keys:` statt `(client_name, ssn_ein, selected_return_type)`

  **6f) `preprocessor.update_client_status()` (preprocessor.py:287-298)**:
  - `use_id_only` Variable und if/else entfernen
  - `match = (record.client_id == client_id)` fuer alle Return Types

- **Depends on**: none
- **Validate**: `pytest tests/unit/test_csv_integration.py -v`

### Task 7: UPDATE `debug_ocr.py` — SSN/EIN OCR verbessern

- **Action**: UPDATE
- **Implement**: In der OCR-Schleife (debug_ocr.py:90-95):
  - Import von `_ocr_digits` aus `clickbot.vision` (oder inline: `cv2.resize` + Tesseract-Config)
  - Da `debug_ocr.py` standalone ist, besser inline:
    ```python
    if col_name == "ssn_ein":
        region_np_3x = cv2.resize(region_gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        region_pil = Image.fromarray(region_np_3x)
        text = pytesseract.image_to_string(region_pil, config="--psm 7 -c tessedit_char_whitelist=0123456789-").strip()
    else:
        region_pil = Image.fromarray(region_gray)
        text = pytesseract.image_to_string(region_pil, lang="eng").strip()
    ```
- **Depends on**: none
- **Validate**: `python debug_ocr.py` (manuell, braucht TaxAct)

### Task 8: UPDATE Tests — `normalize_ssn_ein`

- **Action**: UPDATE
- **Implement**: In `tests/unit/test_1120_process.py:338-344`:
  - `test_leading_zero_ein`: Assertion aendern — `normalize_ssn_ein("93871200", "1120")` soll jetzt `"93871200"` zurueckgeben (raw, da 8 Digits != 9)
  - `test_leading_zero_ssn`: Assertion aendern — `normalize_ssn_ein("23456789", "1040")` soll jetzt `"23456789"` zurueckgeben
  - Neuer Test: `test_8_digits_not_padded` — bestaetigt dass 8 Digits nicht mehr gepadded werden
- **Depends on**: Task 5
- **Validate**: `pytest tests/unit/test_1120_process.py -v -k "normalize_ssn_ein"`

### Task 9: UPDATE Tests — CSV Matching (ID-only)

- **Action**: UPDATE
- **Implement**: In `tests/unit/test_csv_integration.py`:

  **9a) `TestScanVisibleClientsCsv` (Zeile 84-275)**:
  - Tests die Composite-Keys verwenden, auf ID-only Keys umstellen
  - `test_skips_non_todo_csv_client`: CSV-Record Key ist jetzt nur `(client_id,)`
  - `test_finds_todo_csv_client`: Analog
  - `test_auto_status_update_collected`: Key Assertion anpassen

  **9b) `TestScanVisibleClientsCsvNew` (Zeile 429-637)**:
  - `test_skips_non_todo_client`: Key basiert jetzt nur auf SSN/EIN
  - `test_skips_client_not_in_csv`: Matching geht nur ueber ID
  - `test_ocr_cleanup_applied`: SSN normalization bleibt, aber Matching nur ueber ID

  **9c) `TestBackwardCompatibility` (Zeile 390-424)**: Unveraendert (In-Memory-Modus ohne CSV)

- **Depends on**: Task 6
- **Validate**: `pytest tests/unit/test_csv_integration.py -v`

### Task 10: UPDATE Tests — Preprocessor `update_client_status`

- **Action**: UPDATE
- **Implement**: In `tests/unit/test_preprocessor.py`:
  - Tests fuer `update_client_status` die bisher Composite-Key testen, auf ID-only anpassen
  - `test_update_matches_composite_key`: Rename zu `test_update_matches_by_client_id` — zwei Clients mit gleicher client_name aber unterschiedlicher client_id, Update matcht nur die richtige ID
- **Depends on**: Task 6
- **Validate**: `pytest tests/unit/test_preprocessor.py -v`

## Testing Requirements

- [ ] `normalize_ssn_ein` gibt 8-Digit-Werte unveraendert zurueck (kein Padding)
- [ ] `normalize_ssn_ein` formatiert 9-Digit-Werte weiterhin korrekt
- [ ] CSV-Scan matcht Clients nur ueber SSN/EIN (ID)
- [ ] Legacy-Scan (`_scan_visible_clients`) matcht ueber ID wenn CSV vorhanden
- [ ] `update_client_status` matcht nur ueber `client_id`
- [ ] Backward-Compat: In-Memory-Modus ohne CSV funktioniert weiterhin
- [ ] Edge case: Gleiche SSN/EIN mit verschiedenen Return Types (sollte theoretisch nicht vorkommen, aber Test sicherstellen)
- [ ] Edge case: OCR gibt leeren String fuer SSN/EIN zurueck → Client wird uebersprungen

**Test Levels**: Unit

## Bug Handling

- Bugs durch DIESE Aenderungen → sofort fixen
- Vorbestehende Bugs → dokumentieren in `.agents/bugs/`, nicht fixen

## Rollback Strategy

1. `git stash` oder `git checkout .` um alle Aenderungen rueckgaengig zu machen
2. Keine Datenbankmigrationen oder externe Abhaengigkeiten betroffen

## Manual Verification

- [ ] `python debug_ocr.py` ausfuehren und SSN/EIN-Erkennung in Output pruefen
- [ ] Bot mit CSV-Modus starten und 3-5 Clients bearbeiten lassen — keine "not in CSV" Skips wegen falscher SSN/EIN
- [ ] Preprocessing ausfuehren und CSV-Export pruefen — SSN/EIN-Werte korrekt

## Notes

- Die `_ocr_digits()` Funktion ist bewusst spezialisiert und nicht generisch. Fuer andere Spalten (client_name, return_type) bleibt die bestehende OCR unveraendert.
- PSM 7 = "Treat the image as a single text line." Perfekt fuer Tabellenzellen.
- 3x Upscaling ist ein guter Kompromiss zwischen Qualitaet und Performance. 2x waere minimal, 4x unnoetig.
- Die Matching-Vereinfachung auf nur `client_id` ist sicher, weil SSN/EIN pro Steuerpflichtigen eindeutig ist. Zwei verschiedene Return Types fuer dieselbe SSN/EIN kommen in der Praxis nicht vor.

## Confidence Score: 9/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 10 | OCR-Pipeline und Matching-Logik sind klar dokumentiert und verstaendlich |
| **External Knowledge** | 9 | Tesseract PSM/Whitelist ist Standard-Wissen, kein Research noetig |
| **Risk** | 8 | Matching-Aenderung ist breaking, aber durch Tests gut abgesichert |
| **Dependencies** | 8 | 5 Dateien betroffen, aber Aenderungen sind isoliert und parallel |
| **Clarity** | 10 | Anforderungen eindeutig: bessere OCR + ID-only Matching |
| **Testability** | 9 | Unit Tests decken alle Pfade ab, manuell mit debug_ocr.py verifizierbar |

**Overall: 9/10** — Klare Anforderungen, bekannte Patterns, gut testbar. Einziges Risiko: Tesseract-Verhalten mit Whitelist auf dem spezifischen TaxAct-Font, aber das ist durch debug_ocr.py schnell verifizierbar.
