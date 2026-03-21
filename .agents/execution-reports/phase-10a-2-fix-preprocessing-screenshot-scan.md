# Execution Report: Fix Preprocessing — Screenshot-Based Page Scan

## Meta
- **Plan file:** `.agents/plans/phase-10a-2-fix-preprocessing-screenshot-scan.md`
- **Date:** 2026-03-21
- **Status:** Completed

## Summary
- **Tasks completed:** 5 / 5
- **Tests written:** 7 (replaced 6 old tests)
- **Tests passing:** 91 / 91

## Files Changed

### Modified
| File | Changes |
|------|---------|
| `clickbot/vision.py` | Added `read_all_rows_from_screenshot()` — reads all visible rows from a single screenshot |
| `clickbot/preprocessor.py` | Refactored `preprocess_table()` — page-by-page scan with stale end-detection |
| `config/settings.json` | Added `post_scroll_delay_s`, removed `scroll_reset_row` and `end_repeat_threshold` |
| `tests/unit/test_preprocessor.py` | Replaced 6 old tests with 7 new tests for page-scan algorithm |

## Tests Added
| Test File | Coverage |
|-----------|----------|
| `test_preprocessor.py::TestPreprocessTablePageScan` | Single-screenshot-per-page, dedup between pages |
| `test_preprocessor.py::TestPreprocessTableKeyPresses` | Verifies max_visible_rows arrow presses per page |
| `test_preprocessor.py::TestPreprocessTableEndDetection` | Stale detection (3x same last client), reset, empty table |

## Validation Results
- [x] Unit tests: 91/91 passed
- [x] JSON config valid

## Divergences from Plan
| Planned | Actual | Reason |
|---------|--------|--------|
| Task 5: Update settings.example.json | Skipped | File has no `preprocessing` block |

## Issues Encountered
None.

## Algorithm Summary

**Before (broken):**
- Read one row → press down → read next row → press down → ...
- Selection highlight (blue) interfered with OCR
- Visual row tracking could desync from actual position

**After (fixed):**
1. Take ONE screenshot → read ALL 20 visible rows from it (no selection highlight)
2. Press down arrow 20x to scroll to next page
3. Take next screenshot → read all rows → dedup overlapping ~9 rows
4. End detection: if last client unchanged after 3 scroll attempts → done

## Manual Verification
- [ ] Bot-GUI "Scan Client Table" starten, Tabelle ist ganz oben
- [ ] Scan erfasst alle Clients (Anzahl vergleichen mit manueller Zählung)
- [ ] Keine Misreads (kein 'â€"' oder ähnlicher Müll)
- [ ] CSV enthält keine Duplikate
- [ ] Scan stoppt am Ende der Tabelle (nicht endlos)
- [ ] Stop-Button unterbricht Scan sofort

## Next Steps
- E2E-Test gegen echtes TaxAct durchführen
- Bei Bedarf `post_scroll_delay_s` anpassen wenn TaxAct langsam rendert
