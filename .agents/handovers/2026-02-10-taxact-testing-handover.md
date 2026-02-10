# Handover: TaxAct Bot Testing - 2026-02-10

## Kontext

Der TaxAct E-File Extension Bot wurde erstmals gegen echtes TaxAct 2025 Professional getestet. Dieses Dokument fasst den Stand und die nächsten Schritte zusammen.

---

## Wichtige Entscheidung: Simulator verworfen

### Phase 4/4b (TaxAct Simulator) wird NICHT weiter verfolgt

**Grund:** Direktes Testen gegen echtes TaxAct ist möglich und liefert zuverlässigere Ergebnisse.

**Ursprünglicher Plan:**
- Phase 4: Simulator mit Screenshots als UI-Elemente → Screenshots waren korrupt
- Phase 4b: Simulator mit styled Buttons → Unnötig, da direkter TaxAct-Zugang besteht

**Neue Strategie:**
- Direktes Testen gegen TaxAct auf Remote-PC
- Kalibrierung der Koordinaten anhand echter TaxAct-Screenshots
- Iteratives Debugging mit `debug_ocr.py` Script

**Betroffene Dateien (können gelöscht werden):**
- `simulator/` Ordner (komplett)
- `.agents/plans/phase-4-mockup-mode.md`
- `.agents/plans/phase-4b-taxact-simulator-refactor.md`
- `.agents/execution-reports/phase-4-mockup-mode.md`

---

## Aktueller Stand

### Was funktioniert ✅

| Feature | Status | Details |
|---------|--------|---------|
| Bot GUI starten | ✅ | `python -m clickbot.gui` |
| Template Matching | ✅ | 99.6% - 100% Confidence für Column Headers |
| Tesseract OCR | ✅ | Installiert und konfiguriert |
| Column Header Detection | ✅ | Alle 3 Spalten gefunden |
| Explizite X-Koordinaten | ✅ | Config-basiert statt Template Matching |

### Was in Arbeit ist 🔄

| Feature | Status | Problem |
|---------|--------|---------|
| Client Table OCR | 🔄 | Koordinaten kalibriert, muss getestet werden |
| Client-Erkennung | 🔄 | Wartet auf OCR-Test |
| Doppelklick auf Client | ❓ | Noch nicht getestet |
| E-File Prozess Durchlauf | ❓ | Noch nicht getestet |

### Was noch fehlt ❌

- Guardrails (Verifikation nach jedem Klick)
- Error Recovery
- Loop-Modus (mehrere Clients nacheinander)

---

## Remote-PC Setup

### Installierte Software

```
PC: Remote Desktop (TaxAct läuft dort)
OS: Windows
Python: 3.11
Tesseract: 5.4.0 @ C:\Users\michailmoroz\AppData\Local\Programs\Tesseract-OCR\
```

### Projekt-Pfad

```
C:\Users\michailmoroz\taxact-bot\taxact-bot
```

### Wichtig: Tesseract PATH

Bei jeder neuen PowerShell-Session ausführen:
```powershell
$env:PATH += ";C:\Users\michailmoroz\AppData\Local\Programs\Tesseract-OCR"
```

---

## Kalibrierte Koordinaten

Die OCR-Regionen wurden manuell kalibriert für TaxAct auf dem Remote-PC:

```json
"client_table": {
  "row_height": 25,
  "header_row_y": 145,
  "first_data_row_y": 205,
  "max_visible_rows": 20,
  "columns": {
    "client_name": { "x": 20, "width": 330 },
    "return_type": { "x": 470, "width": 51 },
    "fed_ef_status": { "x": 700, "width": 120 }
  }
}
```

### Region-Format erklärt

```
(x1, y1, x2, y2) = (x, y, x + width, y + row_height)
```

Beispiel für return_type:
- x1 = 470 (linke Kante)
- y1 = 205 (obere Kante, erste Datenzeile)
- x2 = 470 + 51 = 521 (rechte Kante)
- y2 = 205 + 25 = 230 (untere Kante)

---

## Debug-Workflow

### 1. Debug-Script auf Remote-PC

Datei `debug_ocr.py` im Projekt-Root erstellen:

```python
"""Debug script to see what OCR captures."""
import pyautogui
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\michailmoroz\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

print("Taking screenshot...")
screenshot = pyautogui.screenshot()
screenshot.save("debug_full_screenshot.png")

# Werte aus config/settings.json
first_data_row_y = 205
row_height = 25

regions = {
    "client_name": (20, first_data_row_y, 20 + 330, first_data_row_y + row_height),
    "return_type": (470, first_data_row_y, 470 + 51, first_data_row_y + row_height),
    "fed_ef_status": (700, first_data_row_y, 700 + 120, first_data_row_y + row_height),
}

print("\nCapturing regions...")
for name, (x1, y1, x2, y2) in regions.items():
    print(f"\n{name}: region ({x1}, {y1}, {x2}, {y2})")
    region = screenshot.crop((x1, y1, x2, y2))
    filename = f"debug_{name}.png"
    region.save(filename)
    text = pytesseract.image_to_string(region, lang='eng').strip()
    print(f"  OCR result: '{text}'")

print("\nDone!")
```

### 2. Koordinaten anpassen

1. `debug_ocr.py` ausführen
2. `debug_*.png` Bilder prüfen
3. Falls falsch: X-Koordinaten in `config/settings.json` anpassen
4. Wiederholen bis korrekt

### 3. Bot testen

```powershell
cd C:\Users\michailmoroz\taxact-bot\taxact-bot
python -m clickbot.gui
```

---

## Git Workflow

### Von lokalem PC pushen

```bash
cd C:\dev\tmaccountant\clickbot_1
git add -A
git commit -m "Beschreibung"
git push
```

### Auf Remote-PC pullen

```powershell
cd C:\Users\michailmoroz\taxact-bot\taxact-bot
git checkout -- .  # Lokale Änderungen verwerfen
git pull
```

---

## Nächste Schritte

### Priorität 1: OCR-Test abschließen

1. Auf Remote-PC: `git pull`
2. Bot starten
3. Prüfen ob Client erkannt wird
4. Falls nicht: Koordinaten weiter kalibrieren

### Priorität 2: Ersten E-File Durchlauf testen

1. Bot startet und erkennt Client
2. Doppelklick auf Client
3. Bot navigiert durch E-File Prozess
4. Beobachten wo es scheitert

### Priorität 3: Guardrails implementieren

```python
# Nach jedem Klick verifizieren:
def execute_step_with_verification(step):
    execute_action(step)
    if not verify_screen_changed(step["expected_screen"]):
        handle_error()
```

---

## Bekannte Probleme

### 1. Tesseract nicht im PATH

**Symptom:** `TesseractNotFoundError`

**Lösung:**
```powershell
$env:PATH += ";C:\Users\michailmoroz\AppData\Local\Programs\Tesseract-OCR"
```

### 2. OCR liest falsche Bereiche

**Symptom:** OCR-Ergebnis enthält Text aus benachbarter Spalte

**Lösung:** X-Koordinaten in `config/settings.json` anpassen

### 3. Git Pull Konflikt

**Symptom:** `error: Your local changes would be overwritten`

**Lösung:**
```powershell
git checkout -- .
git pull
```

---

## Wichtige Dateien

| Datei | Zweck |
|-------|-------|
| `clickbot/vision.py` | OCR und Template Matching |
| `clickbot/bot_controller.py` | Bot-Logik und Thread-Steuerung |
| `clickbot/process_executor.py` | Step-by-Step Prozess-Ausführung |
| `config/settings.json` | Alle Konfiguration inkl. Koordinaten |
| `config/processes/1120.json` | E-File Prozess Definition |

---

## Kontakt-Punkte im Code

### Client-Erkennung

`clickbot/vision.py:592` - `find_next_client()`

### OCR-Region-Berechnung

`clickbot/vision.py:566` - `read_cell()` in `scan_table_row()`

### Prozess-Ausführung

`clickbot/process_executor.py` - `execute_process()`

---

*Handover erstellt: 2026-02-10 18:45 UTC*
