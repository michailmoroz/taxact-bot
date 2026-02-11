# Product Requirements Document (PRD)
# TaxAct E-File Extension Bot

**Version:** 2.5
**Date:** 2026-02-04
**Last Updated:** 2026-02-11
**Author:** Claude Code
**Status:** Draft

> **v2.5 Changes:** Phase 4 (Client Selection) als COMPLETE markiert, Plan/Report-Dateien korrekt benannt
>
> **v2.4 Changes:** Mock-up Modus verworfen (direktes Testen gegen TaxAct möglich), Phasen neu nummeriert
>
> **v2.3 Changes:** .exe Packaging in Scope aufgenommen
>
> **v2.2 Changes:** UI-Sprache auf Englisch umgestellt (GUI und CLI)
>
> **v2.1 Changes:** GUI als Phase 2 vorgezogen, Terminologie vereinfacht (Fokus auf Return-Types 1120/1120S)
>
> **v2.0 Changes:** Multi-Return-Type Support (1120, 1120S), automatische Return-Type Erkennung via OCR, GUI mit Start-Button und Countdown

**UI Language:** English

---

## 1. Executive Summary

Der TaxAct E-File Extension Bot ist ein Desktop-Automatisierungstool, das den repetitiven Prozess der elektronischen Einreichung von Steuerverlängerungen (E-File Extensions) in TaxAct 2025 Professional Edition automatisiert. Der Bot navigiert durch eine Sequenz von ca. 20+ Klicks pro Client, füllt bei Bedarf statische Formulardaten aus und verarbeitet systematisch alle Clients in der Client-Liste.

**Der Bot arbeitet Return-Type-basiert:** Je nach Return-Type (1120 oder 1120S) wird automatisch die passende Klickabfolge ausgewählt und ausgeführt.

Das Tool löst das Problem manueller, zeitaufwändiger Klickarbeit für Steuerberater, die viele Corporate Tax Returns bearbeiten müssen. Durch Automatisierung des E-File-Extension-Prozesses wird die Produktivität erheblich gesteigert und menschliche Fehler bei repetitiven Aufgaben minimiert.

### Unterstützte Return-Types

| Return-Type | Form | Beschreibung |
|-------------|------|--------------|
| **1120** | Form 1120 | U.S. Corporation Income Tax Return |
| **1120S** | Form 1120-S | U.S. Income Tax Return for an S Corporation |

Der Bot erkennt **automatisch** den Return-Type jedes Clients aus der Client-Tabelle via OCR und wählt die entsprechende Klickabfolge. Der Benutzer muss den Return-Type nicht manuell auswählen.

**MVP Goal:** Ein funktionierender Bot mit GUI, der automatisch den Return-Type erkennt, die passende Klickabfolge ausführt und im Loop-Modus mehrere Clients verschiedener Return-Types nacheinander bearbeitet, ohne denselben Client doppelt zu verarbeiten.

---

## 2. Mission

### Mission Statement
Automatisierung des TaxAct E-File-Extension-Prozesses für Return-Types 1120 und 1120S, um Steuerberatern Zeit zu sparen und die Effizienz bei der Massenverarbeitung von Corporate Tax Extensions zu maximieren.

### Core Principles

1. **Zuverlässigkeit** - Der Bot muss den Prozess konsistent und fehlerfrei durchlaufen
2. **Transparenz** - Im Dev-Mode soll der Benutzer jeden Schritt visuell nachvollziehen können
3. **Erweiterbarkeit** - Die Architektur muss Änderungen am Prozess ohne Code-Änderungen ermöglichen
4. **Sicherheit** - Duplikat-Vermeidung durch intelligentes Client-Tracking zur Laufzeit
5. **Feedback** - Akustische Signale für Erfolg, Fehler und Abschluss

---

## 3. Target Users

### Primary Persona: Steuerberater / Tax Preparer

**Profil:**
- Arbeitet mit TaxAct 2025 Professional Edition
- Verarbeitet viele Corporate Tax Returns (Form 1120)
- Muss regelmäßig Form 7004 Extensions für mehrere Clients einreichen
- Technisches Komfortniveau: Mittel (kann Python-Scripts ausführen, aber kein Entwickler)

**Pain Points:**
- Repetitive Klickarbeit für jeden einzelnen Client
- Hoher Zeitaufwand bei vielen Clients
- Fehlerrisiko bei manueller Wiederholung
- Keine native Batch-Funktion in TaxAct für diesen spezifischen Workflow

**Needs:**
- Automatisierung des repetitiven Prozesses
- Visuelle Kontrolle während der Entwicklung/Tests
- Akustisches Feedback über Fortschritt
- Robuste Duplikat-Vermeidung

---

## 4. MVP Scope

### In Scope

#### Core Functionality
- ✅ Automatische Navigation durch den Form 7004 E-File Prozess (~20+ Klicks)
- ✅ Doppelklick auf Client mit leerem "Fed EF Status" in der Client-Liste
- ✅ OCR-basierte Erkennung von leeren Fed EF Status Feldern
- ✅ OCR-basierte Prüfung ob Signing Officer Felder befüllt sind
- ✅ Statische Texteingabe für Officer-Daten (First name, Last name, Email)
- ✅ Scroll-Unterstützung innerhalb von Formularen
- ✅ Bedingte Logik (If/Else) basierend auf Bildschirminhalt
- ✅ Rückkehr zum Client Manager nach jeder Iteration

#### Multi-Return-Type Support (NEU in v2.0)
- ✅ **Automatische Return-Type Erkennung** via OCR aus Client-Tabelle
- ✅ Unterstützung für **Form 1120** (Corporation)
- ✅ Unterstützung für **Form 1120S** (S-Corporation)
- ✅ Separate Klickabfolgen pro Return-Type (JSON-Konfiguration)
- ✅ Dynamische Prozess-Auswahl basierend auf erkanntem Return-Type

#### Client Tracking
- ✅ In-Memory Client-Tracking (Set zur Laufzeit)
- ✅ Duplikat-Vermeidung über Client-Namen
- ✅ Scrollen in Client-Liste wenn nötig
- ✅ Automatische Erkennung wenn alle Clients bearbeitet wurden

#### User Experience
- ✅ Cursor-Visualisierung im Dev-Mode (farbiger Indikator)
- ✅ Sound-Feedback: Success, Error, Complete
- ✅ Hotkey-Steuerung (Start, Stop, Pause)
- ✅ Konfigurierbarer Dev-Mode (ein/ausschaltbar)

#### GUI (NEU in v2.0)
- ✅ **Desktop-Anwendung** mit Tkinter
- ✅ **Start Bot Button** - Startet den Automatisierungsprozess
- ✅ **5-Sekunden Countdown** - Zeit zum Wechseln zu TaxAct
- ✅ **Status-Anzeige** - Zeigt aktuellen Client und Return-Type
- ✅ **Stop Button** - Sofortiger Abbruch
- ✅ **TaxAct 2025 Validierung** - Prüft exakte Version vor Start

#### Technical
- ✅ Konfigurationsdatei für Prozess-Definition (JSON)
- ✅ **Separate Prozess-Dateien pro Return-Type** (1120.json, 1120S.json)
- ✅ Separate Settings für globale Einstellungen
- ✅ Koordinaten-Recorder Tool zum Aufnehmen neuer Positionen

#### Element Detection (NEU in v2.2 - Hybrid Approach)
- ✅ **Primär: Bildbasierte Erkennung** via OpenCV Template Matching
- ✅ **Fallback: Koordinaten** wenn Bild nicht gefunden
- ✅ **Confidence Threshold** konfigurierbar (Standard: 0.8)
- ✅ **Gemeinsame Button-Bibliothek** für alle Return-Types
- ✅ **Scroll-until-visible** - Scrollt bis Element sichtbar
- ✅ **Error Handling:** Element nicht gefunden → Error-Sound + Bot stoppt

#### Multi-Monitor & Startup
- ✅ Unterstützung für Single- und Multi-Monitor-Setups
- ✅ Automatische TaxAct-Fenster-Erkennung beim Start
- ✅ Validierung: TaxAct muss auf Primary Monitor sein (x < 1920)
- ✅ Voraussetzung: TaxAct bereits geöffnet im Client Manager View
- ✅ Fehler mit Sound-Feedback wenn TaxAct nicht korrekt positioniert
- ✅ Start-Check für Bildschirmauflösung (1920x1080 erwartet)

#### Deployment (NEU in v2.3)
- ✅ **Executable (.exe) Packaging** - Standalone Windows-Anwendung via PyInstaller
- ✅ **Keine Python-Installation nötig** - Endbenutzer braucht nur die .exe
- ✅ **Einzelne Datei** - Alle Dependencies gebündelt

### Out of Scope (Future Phases)

#### Deferred Features
- ❌ Persistente Speicherung bearbeiteter Clients (Datei/Datenbank)
- ❌ Automatischer Start mit Windows
- ❌ Dynamische Officer-Daten aus externen Quellen (CSV, API)
- ❌ Parallele Verarbeitung mehrerer TaxAct-Instanzen
- ❌ Remote-Steuerung des Bots
- ❌ Automatische TaxAct-Fenster-Positionierung
- ❌ State Extension (nur Federal Extension im MVP)

---

## 5. User Stories

### Primary User Stories

**US-1: Einzelne Iteration ausführen**
> Als Steuerberater möchte ich eine einzelne Form 7004 E-File Iteration für einen Client ausführen, so dass ich den Bot-Ablauf testen und verifizieren kann.

*Beispiel:* Bot startet bei Client Manager, wählt "10075 SANDMEYER INC", durchläuft alle Screens bis zur E-File Submission, kehrt zum Client Manager zurück.

---

**US-2: Loop-Modus für mehrere Clients**
> Als Steuerberater möchte ich den Bot im Loop-Modus laufen lassen, so dass er automatisch alle Clients mit leerem Fed EF Status nacheinander bearbeitet.

*Beispiel:* Nach Bearbeitung von Client 1 wählt der Bot automatisch Client 2 aus der Liste und wiederholt den Prozess.

---

**US-3: Duplikat-Vermeidung**
> Als Steuerberater möchte ich sicherstellen, dass der Bot keinen Client doppelt bearbeitet, so dass keine fehlerhaften Mehrfach-Submissions entstehen.

*Beispiel:* Wenn "10075 SANDMEYER INC" bereits bearbeitet wurde (auch wenn Alert fehlschlug), wird dieser Client übersprungen und der nächste genommen.

---

**US-4: Visuelle Nachverfolgung (Dev-Mode)**
> Als Entwickler/Tester möchte ich die Mausbewegungen des Bots visuell sehen, so dass ich nachvollziehen kann, wo geklickt wird.

*Beispiel:* Ein roter Kreis erscheint an jeder Klickposition bevor der Klick ausgeführt wird.

---

**US-5: Akustisches Feedback**
> Als Steuerberater möchte ich akustische Signale bei Erfolg, Fehler und Abschluss hören, so dass ich nicht ständig den Bildschirm beobachten muss.

*Beispiel:*
- Erfolg (eine Iteration): Kurzer Beep
- Fehler: Dreifacher tiefer Alarm-Ton
- Komplett fertig: Aufsteigende Melodie

---

**US-6: Automatische Texteingabe**
> Als Steuerberater möchte ich, dass der Bot automatisch die Signing Officer Daten einträgt wenn Felder leer sind, so dass der Prozess nicht unterbrochen wird.

*Beispiel:* Wenn "First name" leer ist, gibt der Bot "testFirstName1" ein, analog für Last name und Email.

---

**US-7: Scrollen in Formularen**
> Als Steuerberater möchte ich, dass der Bot automatisch in langen Formularen scrollt, so dass alle Buttons erreichbar sind.

*Beispiel:* Auf dem "Tax Liability and Payments" Screen scrollt der Bot nach unten um den "Continue" Button zu erreichen.

---

**US-8: Hotkey-Steuerung**
> Als Steuerberater möchte ich den Bot jederzeit per Tastendruck stoppen können, so dass ich bei Problemen sofort eingreifen kann.

*Beispiel:* F7 stoppt den Bot sofort, F6 startet ihn, F8 pausiert.

---

**US-9: Automatische Return-Type Erkennung (NEU v2.0)**
> Als Steuerberater möchte ich, dass der Bot automatisch den Return-Type (1120 oder 1120S) jedes Clients erkennt, so dass ich nicht für jeden Return-Type den Bot separat starten muss.

*Beispiel:* Die Client-Liste enthält 50 Clients - 30x Form 1120 und 20x Form 1120S. Der Bot scannt die "Return Type" Spalte, erkennt automatisch den Typ und führt die passende Klickabfolge aus.

---

**US-10: GUI mit Start-Button (NEU v2.0)**
> Als Steuerberater möchte ich eine einfache Benutzeroberfläche mit einem Start-Button, so dass ich den Bot ohne Terminal-Kenntnisse bedienen kann.

*Beispiel:* Ich öffne die Anwendung, klicke "Start Bot", sehe einen 5-Sekunden Countdown, wechsle zu TaxAct, und der Bot beginnt automatisch.

---

**US-11: Status-Anzeige während der Ausführung (NEU v2.0)**
> Als Steuerberater möchte ich sehen, welchen Client der Bot gerade bearbeitet und welchen Return-Type er erkannt hat, so dass ich den Fortschritt verfolgen kann.

*Beispiel:* GUI zeigt: "Bearbeite: SANDMEYER INC (1120) - Client 5 von 50"

---

### Technical User Stories

**TUS-1: Koordinaten-Aufnahme**
> Als Entwickler möchte ich ein Tool zum Aufnehmen von Bildschirmkoordinaten, so dass ich den Prozess leicht anpassen kann wenn sich UI-Elemente verschieben.

---

**TUS-2: Konfigurierbare Wartezeiten**
> Als Entwickler möchte ich alle Wartezeiten in einer Konfigurationsdatei definieren, so dass ich sie bei Performance-Problemen anpassen kann ohne Code zu ändern.

---

## 6. Core Architecture & Patterns

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         gui.py                               │
│              (Tkinter GUI, Start/Stop, Countdown)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                    (Entry Point, Loop Control)               │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  executor   │   │   vision    │   │    state    │
│   .py       │   │    .py      │   │    .py      │
│             │   │             │   │             │
│ - click()   │   │ - OCR       │   │ - tracking  │
│ - type()    │   │ - scan      │   │ - processed │
│ - scroll()  │   │   table     │   │   clients   │
└─────────────┘   │ - read      │   └─────────────┘
                  │   return    │
                  │   type      │
                  └─────────────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   overlay   │   │   sounds    │   │  process    │
│    .py      │   │    .py      │   │  _loader.py │
│             │   │             │   │             │
│ - visual    │   │ - beep      │   │ - load by   │
│   click     │   │ - alerts    │   │   return    │
└─────────────┘   └─────────────┘   │   type      │
                                    └─────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │   config/                   │
              │   ├── settings.json         │
              │   └── processes/            │
              │       ├── 1120.json         │
              │       └── 1120S.json        │
              └─────────────────────────────┘
```

### Directory Structure

```
clickbot/
├── main.py              # Entry point, main loop, hotkey handling
├── gui.py               # NEU: Tkinter GUI (Start, Stop, Countdown, Status)
├── executor.py          # Low-level actions (click, type, scroll, wait)
├── vision.py            # OCR and screen reading (pytesseract)
├── process_loader.py    # NEU: Lädt Prozess-JSON basierend auf Return-Type
├── overlay.py           # Cursor visualization for dev mode
├── sounds.py            # Audio feedback (winsound)
├── state.py             # Client tracking (in-memory set)
├── window_validator.py  # TaxAct window detection & monitor validation
├── recorder.py          # Utility: capture screen coordinates
│
├── config/
│   ├── settings.json    # Global settings (dev_mode, hotkeys, waits)
│   └── processes/
│       ├── 1120.json    # NEU: Prozess für Form 1120
│       └── 1120S.json   # NEU: Prozess für Form 1120-S
│
├── data/                # Runtime data (empty, for future use)
│
└── requirements.txt     # Python dependencies

.agents/
└── screenshots/
    ├── return-type-1120/   # Screenshots für Form 1120 Prozess
    │   ├── base.png
    │   ├── stage-1-1.png
    │   └── ...
    └── return-type-1120S/  # Screenshots für Form 1120-S Prozess
        ├── base.png
        └── ...
```

### Key Design Patterns

1. **Configuration-Driven Process**
   - Prozess-Schritte in JSON definiert
   - Änderungen ohne Code-Anpassung möglich

2. **State Machine**
   - Jeder Screen ist ein State
   - Transitions durch definierte Actions

3. **Observer Pattern (Dev-Mode)**
   - Overlay beobachtet Klick-Events
   - Visualisiert ohne Hauptlogik zu beeinflussen

4. **Dependency Injection**
   - Settings werden beim Start geladen
   - Module erhalten Konfiguration als Parameter

### Python-Specific Patterns

```python
# Singleton für State-Management
class ClientTracker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.processed = set()
        return cls._instance

# Context Manager für Dev-Mode Overlay
class ClickVisualizer:
    def __enter__(self):
        if DEV_MODE:
            self.show_overlay()
        return self

    def __exit__(self, *args):
        if DEV_MODE:
            self.hide_overlay()
```

---

## 7. Tools/Features

### Feature 1: Process Executor

**Purpose:** Führt die definierte Klick-Sequenz aus

**Operations:**
- `click(x, y)` - Einzelklick an Position
- `double_click(x, y)` - Doppelklick für Client-Auswahl
- `type_text(text)` - Tastatureingabe
- `scroll(direction, amount)` - Scrollen in Formularen
- `wait(seconds)` - Wartezeit zwischen Aktionen

**Key Features:**
- Alle Aktionen respektieren `DEV_MODE` Einstellung
- Automatische Wartezeit nach jedem Klick
- Fail-Safe: Maus in Ecke → Abbruch

---

### Feature 2: Vision Module (Hybrid Detection)

**Purpose:** Findet UI-Elemente via Bild-Erkennung mit Koordinaten-Fallback

**Operations:**
- `find_element(image, confidence, fallback_coords)` - Hybrid-Suche
- `find_and_click(target)` - Findet und klickt Element
- `scroll_until_visible(image, direction, max_scrolls)` - Scrollt bis Element sichtbar
- `wait_for_element(image, timeout)` - Wartet auf Element

**Key Features:**
- **OpenCV Template Matching** als primäre Erkennung
- **Confidence Threshold** (0.0-1.0, Standard 0.8)
- **Koordinaten-Fallback** wenn Bild nicht gefunden
- **Retry-Mechanismus** mit konfigurierbaren Versuchen
- **Error Handling:** Element nicht gefunden nach Retries → Error-Sound + Stop

**Detection Flow:**
```
find_element(target)
    │
    ▼
┌─────────────────────────────────┐
│ OpenCV Template Matching        │
│ confidence >= threshold (0.8)   │
└─────────────────────────────────┘
    │
    ├─── FOUND ──────────────────→ Return (x, y) center of match
    │
    ▼
┌─────────────────────────────────┐
│ Retry (max 3x, 500ms delay)     │
└─────────────────────────────────┘
    │
    ├─── FOUND ──────────────────→ Return (x, y)
    │
    ▼
┌─────────────────────────────────┐
│ Fallback: Use fallback_coords   │
│ LOG WARNING                     │
└─────────────────────────────────┘
    │
    ├─── Has Fallback ───────────→ Return fallback_coords
    │
    ▼
┌─────────────────────────────────┐
│ ERROR: Element not found        │
│ play_error() + Stop Bot         │
└─────────────────────────────────┘
```

---

### Feature 2b: OCR Module

**Purpose:** Liest Text vom Bildschirm, erkennt Return-Type

**Operations:**
- `scan_client_table()` - Liest Client-Namen, Return-Type und Fed EF Status
- `read_region(x, y, width, height)` - OCR für definierten Bereich
- `is_field_empty(region)` - Prüft ob Textfeld leer ist
- `get_return_type(client_row)` - Erkennt Return-Type (1120, 1120S) aus Tabellenzeile

**Key Features:**
- Tesseract OCR Integration
- Region-basiertes Scanning (nicht ganzer Screen)
- Preprocessing für bessere Erkennung
- **Return-Type Erkennung** aus Client-Tabelle (Spalte "Return Type")

---

### Feature 3: Client State Tracker

**Purpose:** Verhindert Duplikat-Bearbeitung

**Operations:**
- `add_processed(client_name)` - Markiert Client als bearbeitet
- `is_processed(client_name)` - Prüft ob bereits bearbeitet
- `get_processed_count()` - Anzahl bearbeiteter Clients
- `clear()` - Reset (bei Neustart)

**Key Features:**
- In-Memory Set (keine Persistenz)
- Wird bei Bot-Beendigung automatisch geleert
- Thread-safe für zukünftige Erweiterungen

---

### Feature 4: Cursor Overlay (Dev-Mode)

**Purpose:** Visuelle Nachverfolgung der Bot-Aktionen

**Operations:**
- `show_click_indicator(x, y, color)` - Zeigt farbigen Kreis
- `show_movement_trail()` - Zeigt Mausbewegung
- `highlight_region(x, y, w, h)` - Markiert OCR-Region

**Key Features:**
- Tkinter-basiertes transparentes Overlay
- Konfigurierbare Farbe und Größe
- Automatisches Ausblenden nach Klick

---

### Feature 5: Sound Feedback

**Purpose:** Akustische Signale für Status

**Operations:**
- `play_success()` - Kurzer Beep bei Erfolg
- `play_error()` - Alarm bei Fehler
- `play_complete()` - Melodie wenn alle Clients fertig

**Key Features:**
- Windows winsound (keine externen Dependencies)
- Konfigurierbare Frequenzen
- Optional deaktivierbar

---

### Feature 6: Coordinate Recorder

**Purpose:** Utility zum Aufnehmen von Screen-Positionen

**Operations:**
- `start_recording()` - Startet Aufnahme-Modus
- `capture_position()` - Speichert aktuelle Mausposition (Hotkey)
- `export_to_json()` - Exportiert Koordinaten

**Key Features:**
- Hotkey-basierte Aufnahme
- Zeigt aktuelle Position in Echtzeit
- Direkte Integration in Prozess-JSON

---

### Feature 7: Window Validator (Multi-Monitor Support)

**Purpose:** Validiert TaxAct-Fenster Position und Monitor-Setup beim Start

**Operations:**
- `find_taxact_window()` - Sucht TaxAct-Fenster nach Titel
- `is_on_primary_monitor(window)` - Prüft ob Fenster auf Primary Monitor (x < 1920)
- `validate_startup()` - Führt alle Startup-Checks durch
- `get_screen_resolution()` - Gibt aktuelle Bildschirmauflösung zurück

**Key Features:**
- Funktioniert mit Single- und Multi-Monitor-Setups
- Klare Fehlermeldungen wenn TaxAct nicht gefunden oder falsch positioniert
- Sound-Feedback bei Fehlern (play_error)
- Prüft Bildschirmauflösung gegen erwartete 1920x1080

**Startup Flow:**
```
Bot Start
    │
    ▼
┌─────────────────────────┐
│ find_taxact_window()    │
└─────────────────────────┘
    │
    ├─── Nicht gefunden ──→ ERROR: "TaxAct nicht geöffnet"
    │
    ▼
┌─────────────────────────┐
│ is_on_primary_monitor() │
└─────────────────────────┘
    │
    ├─── x >= 1920 ───────→ ERROR: "TaxAct nicht auf Primary Monitor"
    │
    ▼
┌─────────────────────────┐
│ get_screen_resolution() │
└─────────────────────────┘
    │
    ├─── != 1920x1080 ────→ WARNING: "Unerwartete Auflösung"
    │
    ▼
    OK: Bot startet
```

---

### Feature 8: Process Loader (NEU v2.0)

**Purpose:** Lädt und verwaltet Prozess-Definitionen basierend auf Return-Type

**Operations:**
- `load_process(return_type: str)` - Lädt JSON für spezifischen Return-Type
- `get_available_processes()` - Listet alle verfügbaren Return-Types
- `validate_process(process: dict)` - Prüft JSON-Struktur auf Vollständigkeit

**Key Features:**
- Dynamisches Laden von `config/processes/{return_type}.json`
- Fallback auf Default-Prozess wenn unbekannter Return-Type
- Validierung der Prozess-Schritte beim Laden

**Process Selection Flow:**
```
Client gefunden (Fed EF Status leer)
    │
    ▼
┌─────────────────────────┐
│ vision.get_return_type()│
└─────────────────────────┘
    │
    ├─── "1120" ──────────→ load_process("1120")
    │
    ├─── "1120S" ─────────→ load_process("1120S")
    │
    └─── Unbekannt ───────→ ERROR + skip client
```

---

### Feature 9: GUI Application (NEU v2.0)

**Purpose:** Benutzerfreundliche Desktop-Oberfläche für Bot-Steuerung

**Operations:**
- `show_main_window()` - Zeigt Hauptfenster
- `start_bot()` - Startet Countdown und Bot
- `stop_bot()` - Stoppt Bot sofort
- `update_status(message)` - Aktualisiert Status-Anzeige

**GUI Elements:**

| Element | Beschreibung |
|---------|--------------|
| **Titel** | "TaxAct E-File Extension Bot" |
| **Start Button** | Großer grüner Button "Start Bot" |
| **Stop Button** | Roter Button "Stop" (während Ausführung) |
| **Countdown** | 5-4-3-2-1 Anzeige vor Start |
| **Status Label** | "Bereit" / "Bearbeite: CLIENT_NAME (1120)" |
| **Progress** | "Client 5 von 50" |
| **Log Area** | Scrollbare Liste der letzten Aktionen |

**GUI Flow:**
```
┌─────────────────────────────────────────┐
│     TaxAct E-File Extension Bot         │
├─────────────────────────────────────────┤
│                                         │
│         [ START BOT ]                   │
│                                         │
│  Status: Bereit                         │
│  TaxAct: ✓ Gefunden auf Primary Monitor │
│                                         │
├─────────────────────────────────────────┤
│  Log:                                   │
│  > Anwendung gestartet                  │
│  > TaxAct 2025 erkannt                  │
│                                         │
└─────────────────────────────────────────┘

        ↓ Klick auf "Start Bot"

┌─────────────────────────────────────────┐
│     TaxAct E-File Extension Bot         │
├─────────────────────────────────────────┤
│                                         │
│              ▶ 5 ◀                      │
│     Wechsle jetzt zu TaxAct!            │
│                                         │
│         [ ABBRECHEN ]                   │
│                                         │
└─────────────────────────────────────────┘

        ↓ Nach Countdown

┌─────────────────────────────────────────┐
│     TaxAct E-File Extension Bot         │
├─────────────────────────────────────────┤
│                                         │
│           [ STOP ]                      │
│                                         │
│  Status: Bearbeite SANDMEYER INC (1120) │
│  Progress: Client 3 von 47              │
│                                         │
├─────────────────────────────────────────┤
│  Log:                                   │
│  > Client 1: SMITH LLC (1120S) ✓        │
│  > Client 2: JONES CORP (1120) ✓        │
│  > Client 3: SANDMEYER INC (1120)...    │
│                                         │
└─────────────────────────────────────────┘
```

**Key Features:**
- Tkinter-basiert (kein zusätzliches Package nötig)
- Minimalistisches Design
- Echtzeit-Status-Updates
- Log-Historie der bearbeiteten Clients
- Kann minimiert werden (läuft im Hintergrund)

---

## 8. Technology Stack

### Backend/Core

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Hauptsprache |
| PyAutoGUI | 0.9.54+ | Maus/Tastatur-Automation |
| **OpenCV** | **4.8.0+** | **Template Matching (Hybrid Detection)** |
| pytesseract | 0.3.10+ | OCR Engine Wrapper |
| Pillow | 10.0+ | Screenshot/Bildverarbeitung |
| keyboard | 0.13.5+ | Global Hotkeys |
| PyGetWindow | 0.0.9+ | Fenster-Erkennung & Multi-Monitor Support |

### System Requirements

| Requirement | Specification |
|-------------|---------------|
| OS | Windows 10/11 |
| Tesseract OCR | 5.0+ (separat installiert) |
| Display | 1920x1080 (Primary Monitor) |
| TaxAct | 2025 Professional Edition |
| Multi-Monitor | Unterstützt (TaxAct muss auf Primary Monitor sein) |

### Dependencies (requirements.txt)

```
pyautogui>=0.9.54
opencv-python>=4.8.0
numpy>=1.24.0
pytesseract>=0.3.10
Pillow>=10.0.0
keyboard>=0.13.5
PyGetWindow>=0.0.9
customtkinter>=5.2.0
```

### GUI Dependencies

```
# CustomTkinter für moderne GUI
customtkinter>=5.2.0
# Tkinter ist in Python enthalten (Basis für CustomTkinter)
```

### Third-Party Integrations

| Integration | Purpose | Required |
|-------------|---------|----------|
| Tesseract OCR | Text recognition | Yes |
| TaxAct 2025 | Target application | Yes |

---

## 9. Security & Configuration

### Configuration Management

**settings.json:**
```json
{
  "dev_mode": true,
  "show_cursor_overlay": true,
  "overlay_color": "red",
  "overlay_size": 20,
  "default_wait": 2.0,
  "long_wait": 5.0,
  "scroll_wait": 0.5,
  "hotkeys": {
    "start": "F6",
    "stop": "F7",
    "pause": "F8"
  },
  "sounds": {
    "enabled": true,
    "success_freq": 1000,
    "error_freq": 400
  },
  "ocr": {
    "tesseract_path": "C:/Program Files/Tesseract-OCR/tesseract.exe",
    "language": "eng"
  },
  "display": {
    "expected_resolution": [1920, 1080],
    "require_primary_monitor": true,
    "taxact_window_title": "TaxAct"
  }
}
```

**Process Definition (config/processes/1120.json) - Hybrid Format:**
```json
{
  "name": "Form 1120 E-File Extension",
  "return_type": "1120",
  "version": "1.0",
  "static_inputs": {
    "officer_first_name": "testFirstName1",
    "officer_last_name": "testLastName1",
    "officer_email": "testName@testServer1.com"
  },
  "steps": [
    {
      "id": 1,
      "name": "click_efile_menu",
      "action": "click",
      "target": {
        "image": "buttons/efile_menu.png",
        "confidence": 0.85,
        "fallback_coords": [850, 45]
      },
      "wait_after": 2.0
    },
    {
      "id": 5,
      "name": "scroll_to_continue",
      "action": "scroll_until_visible",
      "target": {
        "image": "buttons/continue_green.png",
        "scroll_direction": "down",
        "scroll_amount": -3,
        "max_scrolls": 5
      },
      "wait_after": 1.0
    },
    {
      "id": 10,
      "name": "check_officer_fields",
      "action": "conditional",
      "condition": {
        "type": "field_empty",
        "region": [500, 300, 200, 30]
      },
      "if_true": "fill_officer_data",
      "if_false": "continue"
    }
  ]
}
```

**Button Assets Directory:**
```
assets/
└── buttons/
    ├── common/                    # Shared across all return types
    │   ├── continue_green.png
    │   ├── continue_blue.png
    │   ├── yes_button.png
    │   ├── clients_button.png
    │   └── efile_menu.png
    ├── 1120/                      # Form 1120 specific
    │   ├── start_alerts_1120.png
    │   └── ...
    └── 1120S/                     # Form 1120S specific
        ├── submit_efile.png
        ├── new_return.png
        └── ...
```

### Security Scope

**In Scope:**
- ✅ Keine Speicherung sensibler Daten (nur Client-Namen zur Laufzeit)
- ✅ Fail-Safe: Maus in Bildschirmecke stoppt Bot
- ✅ Hotkey zum sofortigen Abbruch
- ✅ Keine Netzwerk-Kommunikation

**Out of Scope:**
- ❌ Verschlüsselung (nicht benötigt)
- ❌ Authentifizierung (lokales Tool)
- ❌ Audit-Logging (zukünftig)

### Deployment Considerations

- **Installation:** Lokales Python-Script
- **Tesseract:** Muss separat installiert werden
- **Permissions:** Keine Admin-Rechte benötigt
- **TaxAct:** Muss bereits geöffnet und im Vordergrund sein

---

## 10. API Specification

*Nicht anwendbar - reines Desktop-Automatisierungstool ohne API.*

### Internal Module Interfaces

**executor.py:**
```python
def click(x: int, y: int, wait: float = None) -> bool
def double_click(x: int, y: int, wait: float = None) -> bool
def type_text(text: str, interval: float = 0.05) -> bool
def scroll(clicks: int, x: int = None, y: int = None) -> bool
def wait(seconds: float) -> None
```

**vision.py:**
```python
def scan_client_table() -> List[ClientInfo]
def read_region(x: int, y: int, w: int, h: int) -> str
def is_field_empty(x: int, y: int, w: int, h: int) -> bool
```

**state.py:**
```python
def add_processed(client_name: str) -> None
def is_processed(client_name: str) -> bool
def get_next_client(clients: List[ClientInfo]) -> Optional[ClientInfo]
```

**window_validator.py:**
```python
def find_taxact_window() -> Optional[Window]
def is_on_primary_monitor(window: Window) -> bool
def get_screen_resolution() -> Tuple[int, int]
def validate_startup() -> Tuple[bool, str]  # (success, error_message)
```

---

## 11. Success Criteria

### MVP Success Definition

Der MVP ist erfolgreich wenn:
1. Eine vollständige Iteration (1 Client) fehlerfrei durchläuft
2. Der Bot **automatisch den Return-Type erkennt** (1120 vs 1120S)
3. Der Bot die **passende Klickabfolge** für jeden Return-Type ausführt
4. Der Loop-Modus mehrere Clients **verschiedener Return-Types** nacheinander bearbeitet
5. Kein Client doppelt bearbeitet wird
6. Der Bot zuverlässig zum Ausgangspunkt zurückkehrt
7. Die **GUI** funktioniert (Start, Stop, Countdown, Status)

### Functional Requirements

**Startup Validation:**
- ✅ Bot prüft ob TaxAct-Fenster geöffnet ist
- ✅ Bot prüft ob TaxAct auf Primary Monitor ist (x < 1920)
- ✅ Bot prüft Bildschirmauflösung (1920x1080 erwartet)
- ✅ Bot gibt Fehler-Sound und Meldung wenn Validierung fehlschlägt

**Core Process:**
- ✅ Bot startet bei Client Manager Screen
- ✅ Bot identifiziert Client mit leerem Fed EF Status
- ✅ **Bot erkennt Return-Type (1120 oder 1120S) via OCR**
- ✅ **Bot lädt passende Prozess-Definition**
- ✅ Bot navigiert durch alle 20+ Screens (je nach Return-Type)
- ✅ Bot füllt leere Officer-Felder aus
- ✅ Bot scrollt wenn nötig
- ✅ Bot kehrt nach Iteration zu Client Manager zurück
- ✅ Bot überspringt bereits bearbeitete Clients
- ✅ Bot stoppt bei unerwartetem Screen
- ✅ Bot gibt Sound-Feedback

**GUI (NEU v2.0):**
- ✅ Desktop-Anwendung startet und zeigt Status
- ✅ Start-Button mit 5-Sekunden Countdown
- ✅ Stop-Button für sofortigen Abbruch
- ✅ Echtzeit-Anzeige: aktueller Client und Return-Type
- ✅ Progress-Anzeige: "Client X von Y"
- ✅ Log-Bereich mit Historie

### Quality Indicators

| Metric | Target |
|--------|--------|
| Success Rate pro Iteration | > 95% |
| Korrekte Duplikat-Vermeidung | 100% |
| **Return-Type Erkennung** | > 98% |
| Hotkey/Button Response Time | < 500ms |
| OCR Accuracy | > 90% |

### User Experience Goals

- Benutzer startet GUI-Anwendung
- **Benutzer klickt "Start Bot" und hat 5 Sekunden zum Wechseln**
- Benutzer sieht Status und Fortschritt in der GUI
- Benutzer kann Bot jederzeit mit Stop-Button oder F7 stoppen
- Benutzer hört deutliches Feedback
- Dev-Mode zeigt jeden Klick visuell

---

## 12. Implementation Phases

### Phase 1: Foundation (Core Infrastructure) ✅ COMPLETE

**Goal:** Basis-Struktur, Startup-Validierung und einfache Klick-Automation

**Deliverables:**
- ✅ Projekt-Struktur erstellen
- ✅ settings.json und Basis-Konfiguration (inkl. display settings)
- ✅ executor.py mit click, type, scroll
- ✅ sounds.py mit winsound Integration
- ✅ window_validator.py mit TaxAct-Fenster-Erkennung und Monitor-Validierung
- ✅ Einfacher Test: Klick an feste Position

**Validation:**
- Bot erkennt ob TaxAct geöffnet und auf Primary Monitor ist
- Bot gibt Fehler-Sound wenn TaxAct nicht korrekt positioniert
- Bot kann an definierten Koordinaten klicken
- Sound-Feedback funktioniert
- Hotkeys reagieren

---

### Phase 2: GUI Application ✅ COMPLETE

**Goal:** Benutzerfreundliche Desktop-Anwendung als Einstiegspunkt

**Deliverables:**
- ✅ gui.py mit CustomTkinter
- ✅ Start Button mit 5-Sekunden Countdown
- ✅ Stop Button für sofortigen Abbruch
- ✅ Status-Anzeige (aktueller Client, Return-Type)
- ✅ Progress-Anzeige (Client X von Y)
- ✅ Log-Bereich für Historie

**Validation:**
- GUI startet und zeigt TaxAct-Status
- Countdown funktioniert (5-4-3-2-1)
- Status-Updates in Echtzeit
- Stop-Button unterbricht sofort
- Log zeigt bearbeitete Clients

**Hinweis:** GUI wird vor der Automatisierungslogik gebaut. Zunächst zeigt sie nur Status und Countdown - die eigentliche Bot-Logik wird in späteren Phasen integriert.

---

### Phase 3: Single Iteration (1 Return-Type) ✅ COMPLETE

**Goal:** Eine vollständige Iteration (1 Client, 1 Return-Type) funktioniert

**Deliverables:**
- ✅ Process Definition in JSON für Return-Type 1120 (`config/processes/1120.json` - 36 Schritte)
- ✅ Alle Klick-Schritte als Sequenz
- ✅ Scroll-Unterstützung (`scroll_until_visible`)
- ✅ Statische Texteingabe für Officer-Daten
- ✅ Rückkehr zu Client Manager
- ✅ Integration mit GUI (Status-Updates)
- ✅ `vision.py` mit OpenCV Template Matching
- ✅ `process_executor.py` mit Step-by-Step Execution
- ✅ `process_loader.py` für JSON-Laden

**Validation:**
- ✅ Alle Module kompilieren ohne Fehler
- ✅ 27 Button-Screenshots vorhanden
- ✅ E2E-Test gegen echtes TaxAct erfolgreich

---

### Phase 4: OCR & Client Selection ✅ COMPLETE

**Goal:** Bot kann Client-Tabelle lesen und automatisch Client auswählen

**Deliverables:**
- ✅ `ClientRow` Dataclass für Tabellendaten
- ✅ `get_column_positions()` - Spaltenköpfe via Template Matching finden
- ✅ `scan_table_row()` - OCR für einzelne Tabellenzeile
- ✅ `find_next_client()` - Ersten Client mit leerem Fed EF Status finden
- ✅ `client_table` Konfiguration in settings.json (Koordinaten kalibriert)
- ✅ Bot-Controller Integration (scannt Tabelle vor Prozess-Start)

**Validation:**
- ✅ Bot erkennt leeren Fed EF Status korrekt
- ✅ Bot erkennt Return-Type (1120 vs 1120S) korrekt
- ✅ Bot wählt automatisch Client und startet Doppelklick

**Plan:** `.agents/plans/phase-4-client-selection.md`
**Report:** `.agents/execution-reports/phase-4-client-selection.md`

---

### Phase 5: Multi-Return-Type Process Files ⬅️ NEXT

**Goal:** Separate Klickabfolgen für verschiedene Return-Types

**Deliverables:**
- ✅ `config/processes/1120.json` - Prozess für Return-Type 1120 (bereits vorhanden)
- ⬜ `config/processes/1120S.json` - Prozess für Return-Type 1120S
- ⬜ Screenshot-Aufnahme für 1120S Prozess
- ⬜ Validierung beider Abläufe gegen echtes TaxAct

**Validation:**
- Bot führt korrekte Klickabfolge für 1120 aus
- Bot führt korrekte Klickabfolge für 1120S aus
- Wechsel zwischen Return-Types funktioniert nahtlos

---

### Phase 6: Loop Mode & State Tracking

**Goal:** Mehrere Clients verschiedener Return-Types nacheinander

**Deliverables:**
- ⬜ state.py für Client-Tracking
- ⬜ Loop-Modus mit Duplikat-Vermeidung
- ⬜ overlay.py für Dev-Mode Visualisierung
- ⬜ Scroll in Client-Liste
- ⬜ Fehlerbehandlung mit Stopp
- ⬜ recorder.py Utility

**Validation:**
- Bot bearbeitet 5+ Clients verschiedener Return-Types
- Kein Client wird doppelt bearbeitet
- Bot wechselt automatisch zwischen 1120 und 1120S
- Bot stoppt sauber wenn fertig oder bei Fehler

---

### Phase 7: Executable Packaging

**Goal:** Standalone Windows-Anwendung für Endbenutzer

**Deliverables:**
- ⬜ PyInstaller Konfiguration (`clickbot.spec`)
- ⬜ Alle Dependencies gebündelt (OpenCV, Tesseract, CustomTkinter)
- ⬜ Einzelne `.exe` Datei oder Installer
- ⬜ Icon und Metadaten für Windows
- ⬜ Tesseract OCR eingebettet oder als Voraussetzung dokumentiert
- ⬜ Build-Script für automatisierte Erstellung

**Validation:**
- `.exe` startet auf frischem Windows 10/11 ohne Python-Installation
- Alle Funktionen identisch zur Python-Version
- Dateigröße akzeptabel (< 200MB)
- Keine Antivirus-Warnungen (Code-Signing optional)

---

## 13. Future Considerations

### Post-MVP Enhancements

1. **Persistente Client-Liste**
   - Speicherung in Datei für Bot-Restart
   - Wiederaufnahme nach Unterbrechung

2. **State Extension Support**
   - Zusätzlicher Prozess für State Extensions
   - Auswahl Federal/State vor Start

3. **Weitere Return-Types**
   - Form 1040 (Individual)
   - Form 1065 (Partnership)
   - Einfaches Hinzufügen neuer JSON-Dateien

### Integration Opportunities

1. **CSV Import für Officer-Daten**
   - Unterschiedliche Daten pro Client
   - Mapping Client → Officer

2. **Reporting**
   - Log-Datei mit bearbeiteten Clients
   - Fehler-Report

3. **Scheduling**
   - Windows Task Scheduler Integration
   - Automatischer Start zu definierten Zeiten

### Advanced Features (Long-term)

- Remote-Steuerung via API
- Machine Learning für UI-Änderungserkennung
- Automatische Fenster-Positionierung
- Dynamische Koordinaten-Anpassung bei anderen Auflösungen

---

## 14. Risks & Mitigations

### Risk 1: TaxAct UI-Änderungen

**Description:** Updates von TaxAct können UI-Elemente verschieben.

**Impact:** Hoch - Bot klickt an falsche Stellen

**Mitigation:**
- Koordinaten in JSON (leicht anpassbar)
- recorder.py Tool für schnelle Neu-Kalibrierung
- Langfristig: Bildbasierte Erkennung

---

### Risk 2: OCR-Ungenauigkeit

**Description:** Tesseract erkennt Text nicht korrekt.

**Impact:** Mittel - Falsche Client-Auswahl oder Feldprüfung

**Mitigation:**
- Preprocessing (Kontrast, Threshold)
- Definierte Regionen statt Vollbild-Scan
- Fallback auf Koordinaten-basierte Auswahl

---

### Risk 3: Timing-Probleme

**Description:** Screens laden unterschiedlich schnell.

**Impact:** Mittel - Bot klickt bevor Element bereit

**Mitigation:**
- Konfigurierbare Wartezeiten
- Erhöhte Wartezeiten für bekannte langsame Screens
- Zukünftig: Wait-for-Element statt feste Wartezeit

---

### Risk 4: Unerwartete Popups/Dialoge

**Description:** TaxAct zeigt unerwartete Meldungen an.

**Impact:** Hoch - Bot-Ablauf unterbrochen

**Mitigation:**
- Sofortiger Stopp bei unerwartetem Zustand
- Sound-Alert für Benutzer
- Zukünftig: Popup-Erkennung und -Handling

---

### Risk 5: Bildschirmauflösung/Skalierung/Multi-Monitor

**Description:** Andere Auflösung als 1920x1080, Windows-Skalierung, oder TaxAct auf falschem Monitor.

**Impact:** Hoch - Alle Koordinaten falsch

**Mitigation:**
- Feste Anforderung: 1920x1080, 100% Skalierung auf Primary Monitor
- window_validator.py prüft TaxAct-Position beim Start
- Automatische Fenster-Erkennung via PyGetWindow
- Klare Fehlermeldung + Sound wenn TaxAct nicht auf Primary Monitor (x >= 1920)
- Start-Check für Auflösung mit Warnung wenn abweichend
- Multi-Monitor wird unterstützt, solange TaxAct auf Primary ist

---

## 15. Appendix

### A. Process Flow Diagram (Return-Type-basiert)

```
┌─────────────────────────────────────────────────────────────┐
│                      GUI APPLICATION                         │
│  [Start Bot] → Countdown 5-4-3-2-1 → Bot startet            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT MANAGER                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Client Name     │ Return Type │ Fed EF Status          │ │
│  ├─────────────────┼─────────────┼────────────────────────┤ │
│  │ SANDMEYER INC   │ 1120        │ [leer] ← nächster      │ │
│  │ SMITH LLC       │ 1120S       │ [leer]                 │ │
│  │ JONES CORP      │ 1120        │ Submitted (skip)       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
         ▼                                   ▼
  OCR: Return-Type = "1120"          OCR: Return-Type = "1120S"
         │                                   │
         ▼                                   ▼
  load_process("1120")               load_process("1120S")
         │                                   │
         └─────────────────┬─────────────────┘
                           │
                           ▼
              [Form View (1120 oder 1120S)]
                           │
                           ▼ Klick "E-file"
              [E-File Center Popup]
                           │
                           ▼ Klick "Submit Electronic Filing Return"
              [Filing Screen]
                           │
                           ▼ Select "File Extension" + Continue
              [Federal Extension]
                           │
                           ▼ Klick "Yes"
              [Form 7004 - Application]
                           │
                           ▼ Klick "Complete Form 7004"
              [Corporation Name]
                           │
                           ▼ Continue (mehrere Screens, je nach Return-Type)
                           ▼ ...
              [Signing Officer Info]
                           │
                           ▼ Prüfe Felder, ggf. Texteingabe, Continue
              [Officer's Signature]
                           │
                           ▼ Continue
              [ERO Signature]
                           │
                           ▼ Continue
              [Federal E-File Alerts]
                           │
                           ▼ Klick "Start Form 7004 Alerts"
              [Error/Omission Screen]
                           │
                           ▼ Klick "Clients" (ignoriere Error)
              [Client Manager] ← LOOP zurück zum nächsten Client
```

### B. Key Dependencies

| Dependency | Download |
|------------|----------|
| Python 3.10+ | https://python.org |
| Tesseract OCR | https://github.com/UB-Mannheim/tesseract/wiki |
| TaxAct 2025 Professional | https://taxact.com |

### C. Reference Screenshots

Screenshots sind nach Return-Type organisiert:

```
.agents/screenshots/
├── return-type-1120/      # Form 1120 (Corporation)
│   ├── base.png           # Client Manager
│   ├── stage-1-1.png      # E-File Menü
│   ├── stage-1-2.png      # Submit Electronic Filing
│   ├── stage-2-1.png      # Filing Screen
│   └── ...                # Weitere Schritte
│
└── return-type-1120S/     # Form 1120-S (S-Corporation)
    ├── base.png           # Client Manager
    ├── stage-1-1.png      # E-File Menü
    └── ...                # Weitere Schritte (kann abweichen!)
```

**Form 1120 Schritte:**
1. Client Manager (Start/Ende)
2. Form 1120 View
3. E-File Center Popup
4. Filing Screen
5. Federal Extension
6. Form 7004 Application
7-8. Corporation Name
9-10. Homeowners Association
11. Address
12. Federal ID Number
13. Fiscal Year
14. Today's Date
15. No Office in US
16. Section 1.6081-5
17-18. Tax Liability and Payments (Scroll)
19. Payment Amount
20. Print Form 7004
21. Acknowledgment Status
22. Signing Officer Information
23-24. Officer's Signature
25. ERO Signature
26. Federal E-File Alerts
27. Error/Omission
28. Client Manager (Return)

**Form 1120S Schritte (24 Screens):**
1. Client Manager - Doppelklick auf Client
2. Form 1120-S View - Klick "E-File" (Taskleiste)
3. E-File Center Popup - Klick "Submit Electronic Filing Return"
4. Filing - "File Extension" auswählen + Continue
5. Extension Intro - Continue (grün)
6. S Corporation Name - Continue
7. Address - Continue
8. EIN - Continue
9. Calendar Year - "Yes, it's a calendar year" + Continue
10. Who is signing - Continue
11. ERO Statement - Continue
12. Email Notification - Continue
13-14. Extension Payment - **Scroll down**
15. Nach Scroll - Continue
16. Review Alerts - **Start Alerts**
17-18. Alerts Result - **IF** "You're Good to Go" → Continue, **ELSE** → Klick "Clients"
19. E-File Confirm - **Submit E-file**
20. Done/Congrats - Continue
21. State Extension? - Continue
22. Filing Complete - **New Return**
23. Add Client Popup - **X** (schließen)
24. Client Manager (base) - Ende der Iteration

### D. Glossary

| Term | Definition |
|------|------------|
| Fed EF Status | Federal E-File Status - zeigt ob Extension eingereicht |
| Form 7004 | IRS Form for Automatic Extension of Time to File |
| Form 1120 | U.S. Corporation Income Tax Return |
| Form 1120-S | U.S. Income Tax Return for an S Corporation |
| Return-Type | Der Typ des Steuerformulars (1120, 1120S) - bestimmt die Klickabfolge |
| ERO | Electronic Return Originator |
| EFIN | Electronic Filing Identification Number |

---

*End of PRD v2.1*
