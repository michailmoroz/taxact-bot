# Plan: Phase 10a-1 — Fix Preprocessing-Scan Key Input

## User Story

Als Steuerberater möchte ich, dass der Preprocessing-Scan die TaxAct-Tabelle zuverlässig per Pfeiltaste durchnavigiert und per Ctrl+Home an den Anfang scrollt, damit alle Clients korrekt erfasst werden.

## Acceptance Criteria

- [x] `_show_click_splash` ist komplett entfernt (keine `tk.Tk()` im Background-Thread)
- [x] Pfeiltaste-Unten navigiert sichtbar durch die TaxAct-Tabelle
- [ ] Ctrl+Home scrollt die Tabelle vor dem Scan korrekt nach oben
- [x] Bestehende Unit Tests laufen weiterhin
- [x] Bot-Loop und GUI bleiben unverändert

## Context

Der Preprocessing-Scan hatte drei separate Key-Input-Probleme:

1. **`_show_click_splash`** erstellte `tk.Tk()` im Background-Thread (nicht thread-safe), stiehlt Fokus → entfernt
2. **`pyautogui.press('down')`** sendet keine Scan Codes / Extended-Key-Flags → ersetzt durch `pydirectinput`
3. **Ctrl+Home** funktioniert weder mit `pyautogui.hotkey()` (kein Scan Code für Home) noch mit `pydirectinput` (Extended-Key-Flag nur für Pfeiltasten, nicht-atomare Aufrufe mit 100ms Pausen) → ersetzt durch `winkeys.send_ctrl_home()` (atomarer `SendInput` mit korrekten Flags)

## Fix History

| Date | Iteration | Change | Result |
|------|-----------|--------|--------|
| 2026-03-21 | 1 | `keyboard` → `pyautogui` | ❌ pyautogui sendet keine Scan Codes |
| 2026-03-21 | 2 | `_show_click_splash` entfernt | ❌ Fokus war nicht das Hauptproblem |
| 2026-03-21 | 3 | `pyautogui.press('down')` → `pydirectinput.press('down')` | ✅ Pfeiltaste funktioniert |
| 2026-03-21 | 3 | `pyautogui.hotkey('ctrl','home')` → `pydirectinput` | ❌ pydirectinput setzt kein Extended-Flag für Home |
| 2026-03-21 | 4 | Ctrl+Home revert zu `pyautogui.hotkey()` | ❌ pyautogui sendet kein Extended-Flag |
| 2026-03-21 | 5 | Ctrl+Home → `winkeys.send_ctrl_home()` (ctypes atomic SendInput) | ⏳ Pending Test |

## Root Cause Analysis

### Pfeiltaste (gelöst)
PyAutoGUI nutzt `keybd_event()` ohne Scan Codes und ohne `KEYEVENTF_EXTENDEDKEY`. `pydirectinput` nutzt `SendInput()` mit Scan Codes und setzt `KEYEVENTF_EXTENDEDKEY` für Pfeiltasten.

### Ctrl+Home (Iteration 5)
Drei Probleme mit bestehenden Libraries:
1. **pyautogui**: Sendet Home ohne Scan Code und ohne Extended-Flag
2. **pydirectinput**: Setzt `KEYEVENTF_EXTENDEDKEY` **nur** für Pfeiltasten (hardcoded: `if key_name in ['up','left','down','right']`). Home wird ignoriert obwohl es eine Extended Key ist.
3. **pydirectinput Atomarität**: `keyDown('ctrl')` + `press('home')` + `keyUp('ctrl')` = 3 separate `SendInput()`-Aufrufe mit jeweils 100ms PAUSE dazwischen. Nicht atomar.

**Lösung**: `winkeys.py` — eigenes Modul mit `ctypes.windll.user32.SendInput()`. Sendet alle 4 Events (Ctrl↓, Home↓, Home↑, Ctrl↑) in **einem einzigen** `SendInput()`-Call mit korrektem `KEYEVENTF_SCANCODE | KEYEVENTF_EXTENDEDKEY` für Home.

## Dependencies

- **New Packages**: none (ctypes ist stdlib)
- **New Files**: `clickbot/winkeys.py`
- **Affected Modules**: `preprocessor.py`, `clickbot.spec`, `tests/unit/test_preprocessor.py`
- **Breaking Changes**: Nein

## Finaler Stand der Key-Input-Strategie

| Aktion | Modul | Warum |
|--------|-------|-------|
| Mouse click/scroll | `pyautogui` | Maus-Events funktionieren problemlos |
| Arrow Down | `pydirectinput` | SendInput mit Extended-Key-Flag für Pfeiltasten |
| Ctrl+Home | `winkeys` (ctypes) | Atomarer SendInput mit Extended-Key-Flag für Home |

## Confidence Score: 9/10

| Factor | Rating | Notes |
|--------|--------|-------|
| **Codebase Patterns** | 9 | Neues Modul, aber minimale API (eine Funktion) |
| **External Knowledge** | 10 | Microsoft SendInput-Doku ist eindeutig |
| **Risk** | 9 | ctypes SendInput ist die low-level-Garantie |
| **Dependencies** | 9 | Nur ctypes (stdlib), kein neues Package |
| **Clarity** | 10 | Root Cause durch 4 Iterationen bestätigt |
| **Testability** | 7 | Nur manuell gegen TaxAct verifizierbar |

**Overall: 9/10** — Atomarer SendInput mit korrekten Flags ist die zuverlässigste Methode. Durch 4 vorherige Iterationen sind alle anderen Optionen ausgeschlossen.
