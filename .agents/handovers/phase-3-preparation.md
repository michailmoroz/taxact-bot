# Handover: Phase 3 Preparation

**Date:** 2026-02-05
**From:** Previous conversation (PRD update, hybrid approach decision)
**To:** New conversation for Phase 3 implementation

---

## Context Summary

The TaxAct E-File Extension Bot is a desktop automation tool that automates Form 7004 E-File submissions in TaxAct 2025 Professional Edition.

### Completed Phases

| Phase | Status | Key Deliverables |
|-------|--------|------------------|
| Phase 1 | COMPLETE | executor.py, sounds.py, window_validator.py, main.py (CLI) |
| Phase 2 | COMPLETE | gui.py, bot_controller.py (CustomTkinter GUI with countdown) |

### Current State

- GUI works with Start/Stop, 5-second countdown, status display
- Bot runs simulation (5 fake steps) - **no real automation yet**
- All UI text is in **English**
- `skip_taxact_validation: true` in settings for dev mode (TaxAct on remote machine)

---

## Phase 3 Goal

Implement **real automation** for a single client using the **Hybrid Detection Approach**:

1. **Primary:** OpenCV Template Matching (find buttons by image)
2. **Fallback:** Coordinates (if image not found)
3. **Error Handling:** Element not found after retries -> Error sound + Stop bot

---

## Hybrid Detection Architecture

```
find_element(target)
    |
    v
[OpenCV Template Matching, confidence >= 0.8]
    |
    +--- FOUND --> Click at detected position
    |
    v
[Retry 3x with 500ms delay]
    |
    +--- FOUND --> Click at detected position
    |
    v
[Fallback: Use fallback_coords from JSON]
    |
    +--- Has Fallback --> Click at fallback coords + LOG WARNING
    |
    v
[ERROR: Element not found]
    --> play_error()
    --> Stop bot
    --> Show error in GUI
```

---

## What Needs to Be Done

### 1. Add OpenCV to Dependencies

```bash
pip install opencv-python numpy
```

Update `requirements.txt`:
```
opencv-python>=4.8.0
numpy>=1.24.0
```

### 2. Create Vision Module

New file: `clickbot/vision.py`

Functions needed:
- `find_element(image_path, confidence=0.8, fallback_coords=None)` -> (x, y) or None
- `find_and_click(target_dict)` -> bool
- `scroll_until_visible(image_path, direction, max_scrolls)` -> bool
- `take_screenshot()` -> numpy array

### 3. Create Process Loader

New file: `clickbot/process_loader.py`

Functions needed:
- `load_process(return_type: str)` -> dict
- `validate_process(process: dict)` -> bool
- `get_step(process: dict, step_id: int)` -> dict

### 4. Create Process Executor

Update: `clickbot/bot_controller.py`

Replace simulation with real step execution:
- Load process JSON for return type
- Execute each step using vision module
- Send status updates to GUI
- Handle errors (element not found -> stop)

### 5. Create Button Assets

Directory: `assets/buttons/`

User will provide screenshots. Need to crop button images from them.

### 6. Create Process JSON Files

Files needed:
- `config/processes/1120.json` - Form 1120 workflow
- `config/processes/1120S.json` - Form 1120S workflow

---

## Information Needed from User

### For Both Return Types (1120 and 1120S):

1. **Screenshots of each screen** in the workflow
2. **Which button to click** on each screen
3. **Where scrolling is needed** (before which button)
4. **Conditional logic** (e.g., "if alerts show 'You're Good to Go' -> Continue, else -> click Clients")
5. **Differences between 1120 and 1120S** workflows

### Questions to Ask:

- How many screens/steps in the 1120 workflow?
- How many screens/steps in the 1120S workflow?
- Which buttons look the same in both workflows? (can share images)
- What are the Officer field values (first name, last name, email)?
- When checking if Officer fields are empty, which fields exactly?

---

## File Structure After Phase 3

```
clickbot_1/
├── clickbot/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── gui.py               # GUI (existing)
│   ├── bot_controller.py    # Updated with real execution
│   ├── executor.py          # Low-level actions (existing)
│   ├── vision.py            # NEW: Hybrid detection
│   ├── process_loader.py    # NEW: Load process JSON
│   ├── sounds.py            # Audio feedback (existing)
│   └── window_validator.py  # Startup validation (existing)
├── config/
│   ├── settings.json
│   └── processes/
│       ├── 1120.json        # NEW: Form 1120 workflow
│       └── 1120S.json       # NEW: Form 1120S workflow
├── assets/
│   └── buttons/
│       ├── common/          # Shared buttons
│       ├── 1120/            # 1120-specific buttons
│       └── 1120S/           # 1120S-specific buttons
└── ...
```

---

## Process JSON Format (Example)

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
        "image": "common/efile_menu.png",
        "confidence": 0.85,
        "fallback_coords": [850, 45]
      },
      "wait_after": 2.0
    },
    {
      "id": 2,
      "name": "scroll_to_continue",
      "action": "scroll_until_visible",
      "target": {
        "image": "common/continue_green.png",
        "scroll_direction": "down",
        "scroll_amount": -3,
        "max_scrolls": 5
      },
      "wait_after": 1.0
    }
  ]
}
```

---

## Starting the New Conversation

1. Run `/prime` to load project context
2. Share this handover document
3. User provides screenshots and explains workflows
4. Create plan with `/plan-feature`
5. Execute plan with `/execute`

---

## Key Decisions Already Made

| Decision | Choice | Reason |
|----------|--------|--------|
| Detection approach | Hybrid (Image + Fallback) | Robust, maintainable, future-proof |
| Image matching | OpenCV Template Matching | Industry standard, confidence threshold |
| Confidence threshold | 0.8 default | Balance between accuracy and flexibility |
| Error handling | Stop bot + error sound | Safe, user is notified immediately |
| UI language | English | User requirement |
| GUI framework | CustomTkinter | Modern look, dark mode |

---

## PRD Reference

See `.agents/PRD.md` (Version 2.2) for full requirements.

Key sections:
- Section 4: MVP Scope (includes Element Detection)
- Section 7: Feature 2 (Vision Module - Hybrid Detection)
- Section 9: Configuration (Process JSON format, Button assets)
- Section 12: Implementation Phases

---

*End of Handover*
