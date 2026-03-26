# Execution Report: SSN/EIN OCR-Verbesserung & ID-Only Matching

## Meta
- **Plan file:** `.agents/plans/ssn-ein-ocr-fix.md`
- **Date:** 2026-03-26
- **Status:** Completed

## Summary
- **Tasks completed:** 10 / 10
- **Tests written:** 2 (updated existing tests)
- **Tests passing:** 216 / 218 (2 pre-existing failures in stale detection)

## Files Changed

### Modified
| File | Changes |
|------|---------|
| `clickbot/vision.py` | Added `_ocr_digits()` helper; updated OCR in `_crop_and_ocr`, `read_all_rows_from_screenshot`, `_read_single_cell` for SSN/EIN; removed leading-zero padding in `normalize_ssn_ein`; simplified matching to ID-only in `scan_visible_clients_csv` and `_scan_visible_clients` |
| `clickbot/preprocessor.py` | Simplified `update_client_status` matching to ID-only |
| `debug_ocr.py` | Added 3x upscale + digit whitelist + PSM 7 for SSN/EIN column |
| `tests/unit/test_1120_process.py` | Updated `normalize_ssn_ein` tests (8-digit no longer padded) |
| `tests/unit/test_csv_integration.py` | Updated `test_ocr_cleanup_applied` (no padding assumption) |
| `tests/unit/test_preprocessor.py` | Renamed `test_update_matches_composite_key` to `test_update_matches_by_client_id` |

## Validation Results
- [ ] Lint: not run (no ruff configured in project)
- [x] Unit tests: 216/218 passed (2 pre-existing failures)
- [x] Affected tests: 95/95 passed

## Divergences from Plan
| Planned | Actual | Reason |
|---------|--------|--------|
| Tuple keys `(csv_id,)` | Direct string keys `csv_id` | Single-element tuple unnecessary; plain string comparison is simpler and equivalent |

## Pre-existing Bugs (not caused by this change)
| Bug | Location | Notes |
|-----|----------|-------|
| Stale detection tests expect threshold=3 but code uses threshold=1 | `test_preprocessor.py:526,617` | Caused by earlier commit `ef2df2b` |

## Manual Verification
- [ ] `python debug_ocr.py` — SSN/EIN recognition with upscaling
- [ ] Bot CSV-mode run — no "not in CSV" skips for valid clients
- [ ] Preprocessing scan — SSN/EIN values correct in CSV export
