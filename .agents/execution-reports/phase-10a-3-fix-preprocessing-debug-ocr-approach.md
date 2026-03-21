# Execution Report: Fix Preprocessing — debug_ocr-Ansatz übernehmen

## Meta
- **Plan file:** `.agents/plans/phase-10a-3-fix-preprocessing-debug-ocr-approach.md`
- **Date:** 2026-03-21
- **Status:** Completed

## Summary
- **Tasks completed:** 6 / 6
- **Tests written:** 2 new (test_second_page_uses_overlap_start_row, test_first_page_reads_all_rows), 7 updated
- **Tests passing:** 93 / 93

## Files Changed

### Modified
| File | Changes |
|------|---------|
| `clickbot/vision.py` | Refactored `read_all_rows_from_screenshot()` — PIL Image input, RGB→GRAY, coords from settings, `start_row` param, no `break` on empty name |
| `clickbot/preprocessor.py` | Refactored `preprocess_table()` — `pyautogui.screenshot()` direkt, `start_row=overlap_rows` ab Seite 2, removed `vision.get_column_positions()` and `vision.take_screenshot()` calls |
| `config/settings.json` | Added `preprocessing.overlap_rows: 9` |
| `debug_ocr.py` | Changed `NUM_ROWS` from 27 to 20 |
| `tests/unit/test_preprocessor.py` | Updated all preprocess_table tests: removed column_positions mocks, switched to pyautogui.screenshot, added overlap/start_row tests |

## Tests Added
| Test File | Coverage |
|-----------|----------|
| `test_preprocessor.py::TestPreprocessTablePageScan::test_second_page_uses_overlap_start_row` | Verifies start_row=0 on page 1, start_row=overlap_rows on page 2+ |
| `test_preprocessor.py::TestPreprocessTablePageScan::test_first_page_reads_all_rows` | Verifies first page always uses start_row=0 |

## Validation Results
- [x] Unit tests: 93/93 passed
- [x] JSON config valid

## Divergences from Plan
| Planned | Actual | Reason |
|---------|--------|--------|
| Task 6: Update settings.example.json | Skipped | File has no `preprocessing` block |

## Issues Encountered
None.

## Key Changes Summary

**vision.py `read_all_rows_from_screenshot()` — Before vs After:**

| Aspect | Before | After |
|--------|--------|-------|
| Input | BGR numpy array + column_positions dict | PIL Image (RGB) |
| Coords | From template matching (column_positions) | Direct from settings.json |
| Grayscale | RGB→BGR→GRAY | RGB→GRAY (like debug_ocr.py) |
| Empty row | `break` — loses all remaining rows | `continue` — skips row, reads rest |
| Start row | Always 0 | Configurable via `start_row` param |

**preprocessor.py `preprocess_table()` — Before vs After:**

| Aspect | Before | After |
|--------|--------|-------|
| Screenshot | `vision.take_screenshot()` (BGR numpy) | `pyautogui.screenshot()` (PIL RGB) |
| Column headers | `vision.get_column_positions()` required | Not needed (coords from settings) |
| Page 1 | Read all 20 rows | Read all 20 rows (start_row=0) |
| Page 2+ | Read all 20 rows + dedup overlap | Read only rows 9-19 (start_row=overlap_rows) + dedup safety net |

## Manual Verification
- [ ] Bot-GUI "Scan Client Table" starten, Tabelle ganz oben
- [ ] Scan erfasst ALLE Clients (Anzahl vergleichen mit manueller Zählung)
- [ ] Client-Namen korrekt gelesen (Vergleich mit TaxAct)
- [ ] Ab Seite 2: Nur 11 Sound-Beeps pro Seite (nicht 20)
- [ ] CSV enthält keine Duplikate
- [ ] CSV enthält keine fehlenden Clients
- [ ] Scan stoppt am Ende der Tabelle
- [ ] Stop-Button unterbricht Scan sofort

## Next Steps
- E2E-Test gegen echtes TaxAct durchführen
- Bei Bedarf `overlap_rows` anpassen wenn mehr/weniger Overlap beobachtet wird
- Bei Bedarf `post_scroll_delay_s` erhöhen wenn TaxAct nach Scroll noch rendert
