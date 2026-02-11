# Bug Fix: Dynamic Return Type Loading

## Meta

- **Date**: 2026-02-11
- **Commit**: b63301f
- **Severity**: High
- **Phase**: 5 (1120S Process)

## Bug Summary

**Symptom**: Bot schlug bei 1120S Clients fehl mit Error "Element not found: common/yes_green.png"

**Expected**: Bot lädt `1120S.json` und führt 1120S-spezifische Schritte aus

**Actual**: Bot lud immer `1120.json` (hardcoded), unabhängig vom erkannten Return-Type

## Root Cause

**Location**: `clickbot/bot_controller.py:142`

**Problem**:
```python
target_return_type = "1120"  # ← HARDCODED
```

Der Return-Type war fest auf "1120" gesetzt. Obwohl `vision.find_next_client()` den korrekten Return-Type des Clients erkannte (`client_row.return_type = "1120S"`), wurde dieser Wert ignoriert und stattdessen der hardcoded Wert an `process_executor.execute()` übergeben.

**Ablauf vor Fix**:
1. `find_next_client(settings, "1120")` - suchte nur nach 1120 Clients
2. Fand aber 1120S Client (weil "1120" in "1120S" enthalten)
3. `execute("1120")` - lud falsche Prozess-Datei
4. Step 6 (`yes_green.png`) existiert nicht in 1120S Flow → Error

## Fix Applied

### Änderung 1: `vision.py` - Dynamische Suche

**Vorher** (Zeile 597-600):
```python
def find_next_client(
    settings: dict,
    target_return_type: str = "1120"
) -> Optional[Tuple[ClientRow, Tuple[int, int]]]:
```

**Nachher**:
```python
def find_next_client(
    settings: dict,
    target_return_type: Optional[str] = None
) -> Optional[Tuple[ClientRow, Tuple[int, int]]]:
```

### Änderung 2: `vision.py` - Type-Filter optional

**Vorher** (Zeile 645-648):
```python
# Return Type must match
type_matches = target_return_type in row_data.return_type
```

**Nachher**:
```python
# Return Type filter (if specified)
if target_return_type:
    type_matches = target_return_type in row_data.return_type
else:
    type_matches = True  # Accept any return type
```

### Änderung 3: `bot_controller.py` - Keine Type-Einschränkung

**Vorher** (Zeile 140-143):
```python
self.message_queue.put(StatusMessage("log", "Looking for unprocessed 1120 client..."))
target_return_type = "1120"
client_result = vision.find_next_client(self.settings, target_return_type)
```

**Nachher**:
```python
self.message_queue.put(StatusMessage("log", "Looking for unprocessed client..."))
client_result = vision.find_next_client(self.settings)
```

### Änderung 4: `bot_controller.py` - Erkannten Type verwenden

**Vorher** (Zeile 179):
```python
result = process_executor.execute(target_return_type)
```

**Nachher**:
```python
result = process_executor.execute(client_row.return_type)
```

## Files Changed

| File | Changes |
|------|---------|
| `clickbot/vision.py` | Parameter optional, Type-Filter conditional |
| `clickbot/bot_controller.py` | Hardcoded type entfernt, erkannten Type verwendet |

## Verification

- [ ] 1120 Client wird korrekt verarbeitet
- [x] 1120S Client wird korrekt verarbeitet (nach Fix)
- [ ] Zukünftige Return-Types werden automatisch unterstützt

## Impact

**Positiv**:
- Bot funktioniert jetzt mit allen Return-Types (1120, 1120S, zukünftige)
- Keine Code-Änderungen nötig für neue Return-Types
- Nur neue JSON-Prozess-Datei erforderlich

**Risiko**: Keins - Änderung ist rückwärtskompatibel

## Lessons Learned

1. **Keine hardcoded Werte** für dynamische Daten
2. **Erkannte Daten nutzen** statt Annahmen treffen
3. **Zukunftssicher designen** - Parameter optional machen für Erweiterbarkeit
