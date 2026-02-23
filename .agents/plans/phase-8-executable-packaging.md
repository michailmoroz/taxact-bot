# Plan: Phase 8 — Executable Packaging

## User Story

Als Steuerberater möchte ich eine einfache Setup-Datei erhalten, damit ich den Bot auf jedem Windows-PC ohne Python-Installation nutzen kann.

## Acceptance Criteria

- [ ] `pyinstaller --onedir` baut erfolgreich ein `dist/TaxActBot/` Verzeichnis
- [ ] `TaxActBot.exe` startet die GUI auf einem PC ohne Python
- [ ] Alle Assets (Button-Templates, Verify-PNGs, Prozess-JSONs) sind gebündelt und funktionieren
- [ ] Tesseract OCR ist gebündelt (kein separates Installieren nötig)
- [ ] CustomTkinter-Theme-Dateien sind inkludiert
- [ ] `settings.json` wird beim ersten Start nach `%APPDATA%/TaxActBot/` kopiert und von dort gelesen
- [ ] Logs werden nach `%APPDATA%/TaxActBot/logs/` geschrieben
- [ ] Inno Setup Installer erzeugt `TaxActBot_Setup.exe`
- [ ] `build.bat` automatisiert den gesamten Build-Prozess

## Context

Der Bot funktioniert aktuell nur als Python-Script. Für den Endbenutzer (Steuerberater) brauchen wir eine standalone Windows-Anwendung. Wir verwenden PyInstaller im `--onedir`-Modus (CustomTkinter-Kompatibilität) und Inno Setup als kostenlosen Installer.

**Kernproblem:** Alle Module verwenden relative Pfade (`Path("config/...")`, `Path(".agents/screenshots/...")`) die in einem PyInstaller-Bundle nicht funktionieren. Wir brauchen eine zentrale `paths.py` die je nach Kontext (Entwicklung vs. Exe) die richtigen Pfade auflöst.

## Research Summary

### Relevant Files — Pfad-Referenzen die angepasst werden müssen
| File | Pfad-Referenz | Zeile |
|------|---------------|-------|
| `clickbot/main.py` | `Path("config/settings.json")` | 189 |
| `clickbot/main.py` | `Path("logs")` | 68 |
| `clickbot/gui.py` | `Path("config/settings.json")` | 390 |
| `clickbot/vision.py` | `_config["screenshot_base_path"]` (default: `.agents/screenshots/buttons`) | 28, 47 |
| `clickbot/vision.py` | `pytesseract.tesseract_cmd` | 68 |
| `clickbot/process_loader.py` | `Path(f"config/processes/{return_type}.json")` | 41 |
| `clickbot/process_loader.py` | `Path("config/processes")` | 131 |

### Patterns to Follow
- Alle Module nutzen `Path()` für Pfade — konsistentes Pattern
- Config wird in `main.py` und `gui.py` geladen und an Module durchgereicht
- Vision-Modul hat `configure()` und `configure_tesseract()` — Pfade kommen aus Settings

## Dependencies

- **New Packages**: `pyinstaller` (dev only, nicht gebündelt)
- **New Tools**: Inno Setup 6 (kostenlos, für Installer-Erstellung)
- **Affected Modules**: `main.py`, `gui.py`, `vision.py`, `process_loader.py` + neues `paths.py`
- **Breaking Changes**: Nein — `paths.py` liefert im Dev-Modus identische Pfade wie bisher

## Tasks

### Task 1: CREATE `clickbot/paths.py`

- **Action**: CREATE
- **Implement**: Zentrales Pfad-Modul das erkennt ob wir als Bundle oder Source laufen

```python
"""Centralized path resolution for both dev and bundled (PyInstaller) mode."""
import os
import sys
from pathlib import Path

def is_frozen() -> bool:
    """Check if running as PyInstaller bundle."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def get_bundle_dir() -> Path:
    """Get the base directory for bundled read-only assets.

    In dev mode: project root (where clickbot/ lives)
    In exe mode: sys._MEIPASS (temp extraction dir with bundled files)
    """
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

def get_user_data_dir() -> Path:
    """Get the user-writable data directory.

    In dev mode: project root
    In exe mode: %APPDATA%/TaxActBot/
    """
    if is_frozen():
        appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        data_dir = appdata / "TaxActBot"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    return Path(__file__).resolve().parent.parent

# Convenience functions
def get_settings_path() -> Path:
    return get_user_data_dir() / "config" / "settings.json"

def get_default_settings_path() -> Path:
    return get_bundle_dir() / "config" / "settings.json"

def get_processes_dir() -> Path:
    return get_bundle_dir() / "config" / "processes"

def get_log_dir() -> Path:
    log_dir = get_user_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def get_assets_dir() -> Path:
    return get_bundle_dir() / "assets"

def get_buttons_dir() -> Path:
    return get_bundle_dir() / ".agents" / "screenshots" / "buttons"

def ensure_user_config() -> Path:
    """Ensure user config exists. Copy bundled default on first run."""
    user_settings = get_settings_path()
    if not user_settings.exists():
        import shutil
        user_settings.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(get_default_settings_path(), user_settings)
    return user_settings
```

- **Depends on**: none
- **Validate**: `python -c "from clickbot.paths import get_bundle_dir; print(get_bundle_dir())"`

### Task 2: UPDATE `clickbot/main.py` — Pfade über paths.py

- **Action**: UPDATE
- **Implement**:
  - Import `from clickbot import paths`
  - Zeile 68: `Path("logs")` → `paths.get_log_dir()`
  - Zeile 189: `Path("config/settings.json")` → `paths.ensure_user_config()`
- **Depends on**: Task 1
- **Validate**: `python -m clickbot.main` (startet wie bisher)

### Task 3: UPDATE `clickbot/gui.py` — Pfade über paths.py

- **Action**: UPDATE
- **Implement**:
  - Import `from clickbot import paths`
  - Zeile 390: `Path("config/settings.json")` → `paths.ensure_user_config()`
- **Depends on**: Task 1
- **Validate**: `python -m clickbot.gui` (startet wie bisher)

### Task 4: UPDATE `clickbot/process_loader.py` — Pfade über paths.py

- **Action**: UPDATE
- **Implement**:
  - Import `from clickbot import paths`
  - Zeile 41: `Path(f"config/processes/{return_type}.json")` → `paths.get_processes_dir() / f"{return_type}.json"`
  - Zeile 131: `Path("config/processes")` → `paths.get_processes_dir()`
- **Depends on**: Task 1
- **Validate**: `python -c "from clickbot.process_loader import load_process; print(load_process('1120S')['name'])"`

### Task 5: UPDATE `clickbot/vision.py` — Pfade über paths.py

- **Action**: UPDATE
- **Implement**:
  - Import `from clickbot import paths`
  - Default `screenshot_base_path` (Zeile 28): Über `paths.get_buttons_dir()` auflösen
  - In `configure()` (Zeile 47): Relative Pfade gegen `paths.get_bundle_dir()` auflösen
  - In `configure_tesseract()` (Zeile 64-69): Wenn `is_frozen()`, Tesseract im Bundle suchen
  - `base_path` Parameter (für Verify-Templates): Gegen `paths.get_bundle_dir()` auflösen
- **Depends on**: Task 1
- **Validate**: `python -c "from clickbot import vision; print('OK')"`

### Task 6: UPDATE `clickbot/main.py` — `setup_logging()` Log-Pfad

- **Action**: UPDATE
- **Implement**: `setup_logging()` akzeptiert `log_dir` Parameter (default: `paths.get_log_dir()`)
- **Pattern**: Bereits `log_dir = Path("logs")` — einfach ersetzen
- **Depends on**: Task 2
- **Validate**: `python -m clickbot.main` (Log-Datei wird erstellt)

### Task 7: Tesseract Bundle vorbereiten

- **Action**: CREATE
- **Implement**:
  - Erstelle `tesseract_bundle/` Ordner im Projektroot
  - Kopiere aus lokaler Installation: `tesseract.exe`, alle DLLs, `tessdata/eng.traineddata`
  - Dokumentiere in README welche Dateien kopiert werden müssen
  - Alternativ: Script `scripts/prepare_tesseract.bat` das die Dateien automatisch kopiert
- **Depends on**: none
- **Validate**: `tesseract_bundle/tesseract.exe --version`

### Task 8: CREATE `clickbot.spec` — PyInstaller Konfiguration

- **Action**: CREATE
- **Implement**: PyInstaller Spec-Datei mit:
  - Entry point: `clickbot/gui.py`
  - `--onedir` Modus (`exclude_binaries=True` in EXE)
  - `--windowed` (kein Konsolen-Fenster)
  - `datas`: config/, assets/, .agents/screenshots/buttons/
  - `binaries`: tesseract_bundle/
  - `--collect-all customtkinter`
  - `hiddenimports`: `pywintypes`, `cv2`
  - `upx=False` (kein UPX, verhindert AV-Fehlalarme)
  - `uac_admin=True` (keyboard Modul braucht Admin)
  - Icon: `assets/icon.ico` (falls vorhanden)
  - Excludes: `matplotlib`, `scipy`, `pandas` (nicht benötigt)
- **Depends on**: Task 7
- **Validate**: `pyinstaller clickbot.spec` (Build ohne Fehler)

### Task 9: CREATE `scripts/build.bat` — Build-Automatisierung

- **Action**: CREATE
- **Implement**:
```bat
@echo off
echo === Building TaxActBot ===
echo.
echo Step 1: Clean previous build...
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
echo.
echo Step 2: Running PyInstaller...
pyinstaller clickbot.spec --noconfirm
echo.
echo Step 3: Verify output...
if exist dist\TaxActBot\TaxActBot.exe (
    echo SUCCESS: dist\TaxActBot\TaxActBot.exe created
) else (
    echo FAILED: exe not found
    exit /b 1
)
echo.
echo Done! Run dist\TaxActBot\TaxActBot.exe to test.
```
- **Depends on**: Task 8
- **Validate**: `scripts/build.bat` (erzeugt dist/TaxActBot/)

### Task 10: Test — Exe starten und Funktionalität prüfen

- **Action**: Manual verification
- **Implement**:
  - `dist/TaxActBot/TaxActBot.exe` starten
  - GUI erscheint mit CustomTkinter-Theme
  - Settings werden nach `%APPDATA%/TaxActBot/config/` kopiert
  - Logs werden nach `%APPDATA%/TaxActBot/logs/` geschrieben
  - Template-Matching funktioniert (Button-PNGs geladen)
  - Tesseract OCR funktioniert (kein "tesseract not found")
- **Depends on**: Task 9
- **Validate**: Manuell

### Task 11: CREATE `installer/taxactbot.iss` — Inno Setup Script

- **Action**: CREATE
- **Implement**: Inno Setup Script das:
  - `dist/TaxActBot/` als Quelle verwendet
  - Installiert nach `{autopf}\TaxActBot` (Program Files)
  - Desktop-Shortcut erstellt
  - Start-Menü-Eintrag erstellt
  - Uninstaller erzeugt
  - App-Name, Version, Publisher setzt
- **Depends on**: Task 10
- **Validate**: Inno Setup kompiliert `TaxActBot_Setup.exe`

### Task 12: UPDATE PRD — Phase 8 als COMPLETE markieren

- **Action**: UPDATE
- **Implement**: `.agents/PRD.md` — Phase 8 Deliverables mit ✅ markieren
- **Depends on**: Task 11
- **Validate**: grep "Phase 8" .agents/PRD.md

## Testing Requirements

- [ ] `paths.py`: `is_frozen()` returns `False` im Dev-Modus
- [ ] `paths.py`: `get_bundle_dir()` zeigt auf Projektroot im Dev-Modus
- [ ] Alle Module starten wie bisher im Dev-Modus (keine Regression)
- [ ] PyInstaller Build ohne Fehler
- [ ] Exe startet GUI erfolgreich
- [ ] Templates/Assets werden im Bundle gefunden
- [ ] Tesseract funktioniert im Bundle
- [ ] Settings werden nach %APPDATA% kopiert
- [ ] Installer erstellt funktionierenden Shortcut

**Test Levels**: Unit (paths.py) | Integration (Build) | E2E (manuell)

## Bug Handling

- Bugs durch DIESE Änderungen → Sofort fixen
- Vorbestehende Bugs → Dokumentieren in `.agents/bugs/`, NICHT fixen

## Rollback Strategy

1. `git stash` oder `git checkout .` — alle Änderungen rückgängig
2. `paths.py` löschen reicht — alle anderen Module funktionieren mit den alten relativen Pfaden weiter

## Manual Verification

- [ ] `python -m clickbot.gui` startet wie bisher (Dev-Modus, keine Regression)
- [ ] `dist/TaxActBot/TaxActBot.exe` startet GUI
- [ ] Button-Templates werden erkannt
- [ ] Tesseract OCR funktioniert
- [ ] `%APPDATA%/TaxActBot/config/settings.json` existiert nach erstem Start
- [ ] `TaxActBot_Setup.exe` installiert korrekt

## Notes

- **opencv-python-headless** statt `opencv-python` verwenden → kleineres Bundle, keine Qt-Abhängigkeiten
- **UPX deaktiviert** → verhindert Antivirus-Fehlalarme
- **Admin-Rechte nötig** → `keyboard` Modul braucht Admin für globale Hotkeys
- **Tesseract-Bundle ~30MB** → nur `eng.traineddata` inkludieren, nicht alle Sprachen
- **Inno Setup** muss separat installiert sein um den Installer zu bauen (nicht Teil des Python-Builds)
- Task 7 (Tesseract kopieren) und Task 10 (E2E Test) sind manuelle Schritte
