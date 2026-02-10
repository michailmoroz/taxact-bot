---
description: Prime agent with codebase understanding
---

# Prime: Load Project Context (TaxAct Form 7004 Automation Bot)

## Objective

Build comprehensive understanding of the TaxAct Form 7004 E-File Automation Bot - a desktop automation tool that automates the repetitive process of filing tax extensions (Form 7004) in TaxAct 2025 Professional Edition.

## Process

### 1. Analyze Project Structure

Use the Glob tool to show the project's directory structure. Focus on:
- Top-level Python files (main.py, executor.py, vision.py, etc.)
- Config directory (config/)
- Documentation (.agents/)
- Avoid __pycache__, .venv, venv directories

### 2. Read Core Documentation (Priority Order)

**MUST READ:**
- `.agents/PRD.md` - Product requirements, architecture, implementation phases
- `CLAUDE.md` - Development guidelines, coding standards (if exists)
- `README.md` - Project overview, setup instructions (if exists)

**OPTIONAL (for deeper context):**
- `config/settings.json` - Global settings, hotkeys, display config
- `config/processes/taxact_extension.json` - Process step definitions

### 3. Identify Key Files & Configuration

**Core Configuration (READ):**
- `requirements.txt` - Python dependencies
- `config/settings.json` - Dev mode, hotkeys, sounds, OCR, display settings

**Core Modules (SCAN):**
- `main.py` - Entry point, main loop, hotkey handling
- `executor.py` - Click, type, scroll actions (PyAutoGUI)
- `vision.py` - OCR and screen reading (pytesseract)
- `window_validator.py` - TaxAct window detection, multi-monitor validation
- `state.py` - Client tracking (in-memory set)
- `sounds.py` - Audio feedback (winsound)
- `overlay.py` - Cursor visualization for dev mode
- `recorder.py` - Coordinate capture utility

**Process Definition (READ):**
- `config/processes/taxact_extension.json` - Step-by-step process definition

### 4. Check Implementation Status

Based on PRD.md, identify:
- Which implementation phase we're in (1-4)
- Which modules are implemented vs. pending
- Known issues or blockers

### 5. Understand Current Development State

This is a local Python project (no git). Check:
- Which Python files exist
- Whether config files are created
- Any existing test files

## Output Report

Provide a concise, actionable summary:

### 1. Project Identity
- **Name:** TaxAct Form 7004 Automation Bot
- **Purpose:** Automate Form 7004 E-File extension process in TaxAct 2025 Professional
- **Target User:** Tax preparers processing multiple corporate returns
- **Current Phase:** Extract from PRD.md (Phase 1-4)

### 2. Tech Stack
- **Language:** Python 3.10+
- **Automation:** PyAutoGUI (mouse/keyboard)
- **OCR:** pytesseract + Tesseract OCR
- **Window Detection:** PyGetWindow
- **Hotkeys:** keyboard library
- **Sound:** winsound (Windows built-in)

### 3. Architecture Overview
- **Entry Point:** `main.py` - Loop control, hotkey handling
- **Actions:** `executor.py` - click, type, scroll, wait
- **Vision:** `vision.py` - OCR, table scanning, field checking
- **Validation:** `window_validator.py` - Monitor check, TaxAct detection
- **State:** `state.py` - Client tracking (in-memory)
- **Feedback:** `sounds.py` + `overlay.py`

### 4. Module Status
| Module | Status | Purpose |
|--------|--------|---------|
| main.py | ? | Entry point, loop control |
| executor.py | ? | Click/type/scroll actions |
| vision.py | ? | OCR, screen reading |
| window_validator.py | ? | Multi-monitor validation |
| state.py | ? | Client tracking |
| sounds.py | ? | Audio feedback |
| overlay.py | ? | Dev mode visualization |
| recorder.py | ? | Coordinate capture |

### 5. Implementation Phases
| Phase | Name | Status |
|-------|------|--------|
| 1 | Foundation | ? |
| 2 | Single Iteration | ? |
| 3 | OCR & Intelligence | ? |
| 4 | Loop Mode & Polish | ? |

### 6. Key Features (from PRD)
- [ ] TaxAct window detection (Multi-Monitor support)
- [ ] ~20+ click sequence per client
- [ ] OCR for Fed EF Status detection
- [ ] OCR for empty field detection
- [ ] Static text input for Officer data
- [ ] In-memory client tracking (no duplicates)
- [ ] Sound feedback (success, error, complete)
- [ ] Dev mode cursor visualization
- [ ] Hotkey control (F6 start, F7 stop, F8 pause)

### 7. Process Flow Summary
```
Client Manager → E-file → Submit Electronic Filing Return
→ File Extension → Yes → Complete Form 7004
→ [Multiple Continue screens]
→ Signing Officer Info (check/fill fields)
→ Start Form 7004 Alerts → Clients (return)
```

### 8. Immediate Next Steps
Based on current phase, list what needs to be done next.

**Keep it scannable - bullet points, tables, clear sections.**
**Focus on what's IMPLEMENTED vs. PENDING.**
