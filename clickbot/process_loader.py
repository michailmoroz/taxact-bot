"""Process definition loader for automation workflows.

Loads and validates process JSON files that define the automation steps.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Required fields in process definition
REQUIRED_PROCESS_FIELDS = ["name", "return_type", "version"]
REQUIRED_STEP_FIELDS = ["id", "name", "action"]


class ProcessLoadError(Exception):
    """Raised when process loading fails."""
    pass


class ProcessValidationError(Exception):
    """Raised when process validation fails."""
    pass


def load_process(return_type: str) -> Dict[str, Any]:
    """Load a process definition by return type.

    Args:
        return_type: The return type (e.g., "1120", "1120S")

    Returns:
        Process definition dict

    Raises:
        ProcessLoadError: If file not found or invalid JSON
        ProcessValidationError: If process definition is invalid
    """
    process_path = Path(f"config/processes/{return_type}.json")

    if not process_path.exists():
        raise ProcessLoadError(f"Process file not found: {process_path}")

    logger.info(f"Loading process: {process_path}")

    try:
        with open(process_path, "r", encoding="utf-8") as f:
            process = json.load(f)
    except json.JSONDecodeError as e:
        raise ProcessLoadError(f"Invalid JSON in process file: {e}")

    # Validate process
    validate_process(process)

    steps = process.get("stages") or process.get("steps", [])
    logger.info(f"Process loaded: {process['name']} with {len(steps)} steps")
    return process


def validate_process(process: Dict[str, Any]) -> None:
    """Validate a process definition.

    Args:
        process: Process definition dict

    Raises:
        ProcessValidationError: If validation fails
    """
    # Check required fields
    for field in REQUIRED_PROCESS_FIELDS:
        if field not in process:
            raise ProcessValidationError(f"Missing required field: {field}")

    # Support both "stages" (new) and "steps" (legacy) keys
    steps = process.get("stages") or process.get("steps", [])
    if not steps:
        raise ProcessValidationError("Process has no steps/stages")

    for i, step in enumerate(steps):
        for field in REQUIRED_STEP_FIELDS:
            if field not in step:
                raise ProcessValidationError(f"Step {i+1} missing required field: {field}")

        # Validate action type
        valid_actions = ["click", "double_click", "type", "scroll", "scroll_until_visible",
                        "conditional", "wait", "verify_screen", "key_press", "type_field",
                        "multi"]
        if step["action"] not in valid_actions:
            raise ProcessValidationError(f"Step {step['id']} has invalid action: {step['action']}")

    logger.debug(f"Process validation passed: {len(steps)} steps/stages")


def get_step(process: Dict[str, Any], step_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific step by ID.

    Args:
        process: Process definition dict
        step_id: Step ID to find

    Returns:
        Step dict or None if not found
    """
    steps = process.get("stages") or process.get("steps", [])
    for step in steps:
        if step.get("id") == step_id:
            return step
    return None


def get_static_inputs(process: Dict[str, Any]) -> Dict[str, str]:
    """Get static input values from process.

    Args:
        process: Process definition dict

    Returns:
        Dict of static input values
    """
    return process.get("static_inputs", {})


def get_available_processes() -> List[str]:
    """Get list of available process return types.

    Returns:
        List of return type strings
    """
    processes_dir = Path("config/processes")

    if not processes_dir.exists():
        return []

    return [f.stem for f in processes_dir.glob("*.json")]
