"""Process executor for running automation workflows.

Executes steps defined in process JSON with guardrails and error handling.
"""

import logging
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pyautogui
import pyperclip

from clickbot import executor
from clickbot import paths
from clickbot import sounds
from clickbot import vision
from clickbot.bot_controller import StatusMessage
from clickbot.process_loader import load_process, get_static_inputs, ProcessLoadError, ProcessValidationError

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of process execution."""
    success: bool
    steps_completed: int
    total_steps: int
    error_message: Optional[str] = None
    error_step: Optional[int] = None


class ProcessExecutor:
    """Executes automation process steps.

    Handles:
    - Step-by-step execution
    - Guardrails (screen verification)
    - Error handling with sound feedback
    - Status updates via message queue
    """

    def __init__(
        self,
        settings: dict,
        message_queue: queue.Queue,
        stop_event: threading.Event
    ):
        """Initialize the executor.

        Args:
            settings: Settings dict from config/settings.json
            message_queue: Queue for GUI status updates
            stop_event: Event to signal stop
        """
        self.settings = settings
        self.message_queue = message_queue
        self.stop_event = stop_event
        self.current_step = 0
        self.process: Optional[Dict[str, Any]] = None

        # Configure vision module
        vision.configure(settings)
        vision.configure_tesseract(settings)

        logger.debug("ProcessExecutor initialized")

    def execute(self, return_type: str) -> ExecutionResult:
        """Execute a process for the given return type.

        Args:
            return_type: Return type (e.g., "1120")

        Returns:
            ExecutionResult with success status and details
        """
        # Load process
        try:
            self.process = load_process(return_type)
        except (ProcessLoadError, ProcessValidationError) as e:
            self._send_error(f"Failed to load process: {e}")
            return ExecutionResult(
                success=False,
                steps_completed=0,
                total_steps=0,
                error_message=str(e)
            )

        # Support both "stages" (new) and "steps" (legacy) keys
        steps = self.process.get("stages") or self.process.get("steps", [])
        total_steps = len(steps)
        static_inputs = get_static_inputs(self.process)

        self._send_status(f"Starting {self.process['name']}")
        self._send_log(f"Process: {return_type} ({total_steps} steps)")

        # Execute steps
        for i, step in enumerate(steps):
            # Check for stop signal
            if self.stop_event.is_set():
                self._send_log("Execution stopped by user")
                return ExecutionResult(
                    success=False,
                    steps_completed=i,
                    total_steps=total_steps,
                    error_message="Stopped by user"
                )

            self.current_step = i + 1
            step_name = step.get("name", f"Step {step['id']}")
            step_desc = step.get("description", step_name)

            # Terminal debug: clear stage indicator
            logger.info(
                f"[{return_type}] Step {self.current_step:2d}/{total_steps} | "
                f"{step_name:<35s} | {step_desc}"
            )

            self._send_status(f"Step {self.current_step}/{total_steps}: {step_desc}")
            self._send_log(f"Step {self.current_step}/{total_steps}: {step_desc}")

            # Pre-check: optionally verify we're on the right screen
            validation_cfg = self.settings.get("validation", {})
            validation_enabled = validation_cfg.get("enabled", False)
            verify_screen = step.get("verify_screen")
            if verify_screen and validation_enabled:
                on_screen = vision.find_element(
                    verify_screen, fallback_coords=None, retry_count=1,
                    base_path=self._get_verify_base_path()
                )
                if on_screen is None:
                    logger.warning(
                        f"  -> Pre-check: expected screen not detected: {verify_screen}"
                    )

            # Execute step
            success = self._execute_step(step, static_inputs)

            if not success:
                error_msg = f"Step failed: {step_name}"
                self._send_error(error_msg)
                sounds.play_error()
                return ExecutionResult(
                    success=False,
                    steps_completed=i,
                    total_steps=total_steps,
                    error_message=error_msg,
                    error_step=step["id"]
                )

            # Post-step: verify next screen or fall back to wait_after
            verify_next = step.get("verify_next")
            validation_cfg = self.settings.get("validation", {})
            validation_enabled = validation_cfg.get("enabled", False)

            if verify_next and validation_enabled:
                verified = self._wait_and_verify(step, verify_next, validation_cfg)
                if not verified:
                    error_msg = f"Screen verification failed after: {step_name}"
                    self._send_error(error_msg)
                    sounds.play_error()
                    return ExecutionResult(
                        success=False,
                        steps_completed=i,
                        total_steps=total_steps,
                        error_message=error_msg,
                        error_step=step["id"]
                    )
            else:
                # Fallback: fixed wait_after (backward compatible)
                wait_after = step.get("wait_after", self.settings.get("timing", {}).get("default_wait", 2.0))
                if wait_after > 0:
                    time.sleep(wait_after)

        # All steps completed
        self._send_log("All steps completed successfully")
        return ExecutionResult(
            success=True,
            steps_completed=total_steps,
            total_steps=total_steps
        )

    def _execute_step(self, step: Dict[str, Any], static_inputs: Dict[str, str]) -> bool:
        """Execute a single step.

        Args:
            step: Step definition dict
            static_inputs: Static input values

        Returns:
            True if step succeeded, False otherwise
        """
        action = step["action"]
        target = step.get("target", {})

        try:
            if action == "click":
                return self._action_click(target)

            elif action == "double_click":
                return self._action_double_click(target)

            elif action == "type":
                return self._action_type(step, static_inputs)

            elif action == "scroll":
                return self._action_scroll(target)

            elif action == "scroll_until_visible":
                return self._action_scroll_until_visible(target)

            elif action == "conditional":
                return self._action_conditional(step, static_inputs)

            elif action == "wait":
                return self._action_wait(step)

            elif action == "multi":
                return self._action_multi(step, static_inputs)

            elif action == "verify_screen":
                return self._action_verify_screen(target)

            elif action == "key_press":
                return self._action_key_press(step)

            elif action == "type_field":
                return self._action_type_field(step, static_inputs)

            else:
                logger.error(f"Unknown action: {action}")
                return False

        except Exception as e:
            logger.error(f"Step execution error: {e}", exc_info=True)
            return False

    def _action_click(self, target: Dict[str, Any]) -> bool:
        """Execute click action with optional offset."""
        image = target.get("image")
        confidence = target.get("confidence")
        fallback = target.get("fallback_coords")
        offset_x = target.get("offset_x", 0)
        offset_y = target.get("offset_y", 0)

        if fallback:
            fallback = tuple(fallback)

        coords = vision.find_element(image, confidence, fallback)

        if coords is None:
            logger.error(f"Click target not found: {image}")
            return False

        # Apply offset if specified
        click_x = coords[0] + offset_x
        click_y = coords[1] + offset_y

        return executor.click(click_x, click_y, wait=0)  # wait handled by step

    def _action_double_click(self, target: Dict[str, Any]) -> bool:
        """Execute double-click action."""
        image = target.get("image")
        confidence = target.get("confidence")
        fallback = target.get("fallback_coords")

        if fallback:
            fallback = tuple(fallback)

        coords = vision.find_element(image, confidence, fallback)

        if coords is None:
            logger.error(f"Double-click target not found: {image}")
            return False

        return executor.double_click(coords[0], coords[1], wait=0)

    def _action_type(self, step: Dict[str, Any], static_inputs: Dict[str, str]) -> bool:
        """Execute type action."""
        target = step.get("target", {})
        text_key = step.get("text_key")  # Key in static_inputs
        text_value = step.get("text_value")  # Direct value
        clear_first = step.get("clear_first", True)

        # Get text to type
        if text_key and text_key in static_inputs:
            text = static_inputs[text_key]
        elif text_value:
            text = text_value
        else:
            logger.error("No text specified for type action")
            return False

        # Click field first if target specified
        if target:
            image = target.get("image")
            fallback = target.get("fallback_coords")
            if fallback:
                fallback = tuple(fallback)

            coords = vision.find_element(image, target.get("confidence"), fallback)
            if coords:
                executor.click(coords[0], coords[1], wait=0.5)

        # Clear field if requested
        if clear_first:
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.1)

        return executor.type_text(text)

    def _action_scroll(self, target: Dict[str, Any]) -> bool:
        """Execute scroll action."""
        amount = target.get("amount", -3)
        x = target.get("x")
        y = target.get("y")

        return executor.scroll(amount, x, y)

    def _action_scroll_until_visible(self, target: Dict[str, Any]) -> bool:
        """Execute scroll-until-visible action."""
        image = target.get("image")
        confidence = target.get("confidence")
        scroll_x = target.get("scroll_x")
        scroll_y = target.get("scroll_y")
        direction = target.get("scroll_direction", "down")
        max_scrolls = target.get("max_scrolls")

        coords = vision.scroll_until_visible(
            image, confidence, scroll_x, scroll_y, direction, max_scrolls
        )

        return coords is not None

    def _action_conditional(self, step: Dict[str, Any], static_inputs: Dict[str, str]) -> bool:
        """Execute conditional action."""
        condition = step.get("condition", {})
        condition_type = condition.get("type")

        if condition_type == "element_visible":
            # Check if element is visible
            image = condition.get("image")
            confidence = condition.get("confidence")
            # Support "verify" base_path to check against verify templates
            cond_base_path = condition.get("base_path")
            if cond_base_path == "verify":
                cond_base_path = self._get_verify_base_path()
            else:
                cond_base_path = None
            is_visible = vision.find_element(
                image, confidence, fallback_coords=None, base_path=cond_base_path
            ) is not None

            branch = "if_true" if is_visible else "if_false"
            logger.info(f"  -> Condition: {image} visible={is_visible} -> {branch}")

            if is_visible:
                return self._execute_branch(step.get("if_true"), static_inputs)
            else:
                return self._execute_branch(step.get("if_false"), static_inputs)

        elif condition_type == "field_empty_by_label":
            # Check if field is empty using label template (100% screenshot-based)
            label_image = condition.get("label_image")
            field_offset_x = condition.get("field_offset_x", 150)
            field_offset_y = condition.get("field_offset_y", 0)
            field_width = condition.get("field_width", 200)
            field_height = condition.get("field_height", 25)

            is_empty, field_pos = vision.is_field_empty_by_label(
                label_image, field_offset_x, field_offset_y, field_width, field_height
            )

            # Store field position for use in if_true branch
            if field_pos:
                step["_field_position"] = field_pos

            if is_empty:
                return self._execute_branch(step.get("if_true"), static_inputs, field_pos)
            else:
                return self._execute_branch(step.get("if_false"), static_inputs)

        elif condition_type == "checkbox_checked":
            # Check checkbox state using template matching (100% screenshot-based)
            checked_img = condition.get("image_checked")
            unchecked_img = condition.get("image_unchecked")
            confidence = condition.get("confidence")

            is_checked, checkbox_pos = vision.is_checkbox_checked_by_template(
                checked_img, unchecked_img, confidence
            )

            if is_checked is None:
                logger.error("Checkbox not found on screen")
                return False

            if is_checked:
                # Pass position to if_true branch so it can click the checkbox
                return self._execute_branch(step.get("if_true"), static_inputs, checkbox_pos)
            else:
                return self._execute_branch(step.get("if_false"), static_inputs)

        else:
            logger.error(f"Unknown condition type: {condition_type}")
            return False

    def _execute_branch(
        self,
        branch: Any,
        static_inputs: Dict[str, str],
        detected_position: Optional[Tuple[int, int]] = None
    ) -> bool:
        """Execute a conditional branch.

        Args:
            branch: Can be "continue" (do nothing), step dict, or list of steps
            static_inputs: Static input values
            detected_position: Optional (x, y) position from condition check (e.g., checkbox position)

        Returns:
            True if branch executed successfully
        """
        if branch is None or branch == "continue":
            return True

        if isinstance(branch, dict):
            # Single step - inject detected position if action is "click_detected"
            if branch.get("action") == "click_detected" and detected_position:
                result = executor.click(detected_position[0], detected_position[1], wait=0)
            elif branch.get("action") == "type_at_detected" and detected_position:
                # Click at detected position, then type
                executor.click(detected_position[0], detected_position[1], wait=0.5)
                text_key = branch.get("text_key")
                text_value = branch.get("text_value")
                clear_first = branch.get("clear_first", True)

                if text_key and text_key in static_inputs:
                    text = static_inputs[text_key]
                elif text_value:
                    text = text_value
                else:
                    return False

                if clear_first:
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.1)
                    pyautogui.press('delete')
                    time.sleep(0.1)

                result = executor.type_text(text)
            else:
                result = self._execute_step(branch, static_inputs)

            # Verify next screen if branch has verify_next
            if result:
                result = self._verify_branch(branch)

            return result

        if isinstance(branch, list):
            # Multiple steps
            for step in branch:
                if not self._execute_step(step, static_inputs):
                    return False
            # Check verify_next on last step if present
            if branch and isinstance(branch[-1], dict):
                return self._verify_branch(branch[-1])
            return True

        logger.error(f"Invalid branch type: {type(branch)}")
        return False

    def _verify_branch(self, branch: Dict[str, Any]) -> bool:
        """Verify next screen after branch execution if verify_next is set.

        Args:
            branch: Branch dict that may contain verify_next

        Returns:
            True if no verify_next or verification passed
        """
        verify_next = branch.get("verify_next")
        validation_cfg = self.settings.get("validation", {})
        if verify_next and validation_cfg.get("enabled", False):
            if not self._wait_and_verify(branch, verify_next, validation_cfg):
                return False
        return True

    def _action_wait(self, step: Dict[str, Any]) -> bool:
        """Execute wait action."""
        duration = step.get("duration", 1.0)
        time.sleep(duration)
        return True

    def _action_verify_screen(self, target: Dict[str, Any]) -> bool:
        """Execute screen verification."""
        expected = target.get("expected_elements", [])
        confidence = target.get("confidence")

        return vision.verify_screen(expected, confidence)

    def _action_key_press(self, step: Dict[str, Any]) -> bool:
        """Execute key press action (TAB, Enter, etc.)."""
        key = step.get("key", "tab")
        count = step.get("count", 1)

        try:
            for _ in range(count):
                pyautogui.press(key)
                time.sleep(0.1)
            logger.debug(f"Pressed {key} {count}x")
            return True
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False

    def _action_type_field(self, step: Dict[str, Any], static_inputs: Dict[str, str]) -> bool:
        """Type into current field, only if empty.

        Uses clipboard to check if field is empty:
        1. Ctrl+A (select all)
        2. Ctrl+C (copy)
        3. Check clipboard - if empty, type the value
        """
        text_key = step.get("text_key")
        text_value = step.get("text_value")

        # Get text to type
        if text_key and text_key in static_inputs:
            text = static_inputs[text_key]
        elif text_value:
            text = text_value
        else:
            logger.error("No text specified for type_field action")
            return False

        try:
            # Clear clipboard first
            pyperclip.copy("")

            # Select all and copy current content
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.05)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.05)

            # Check clipboard content
            current_content = pyperclip.paste().strip()

            if current_content:
                logger.info(f"Field not empty ('{current_content[:20]}...'), skipping")
                # Press End to deselect and move cursor to end
                pyautogui.press('end')
                return True

            # Field is empty - paste the value via clipboard (most robust method)
            logger.info(f"Field empty, pasting: {text}")
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.1)
            return True

        except Exception as e:
            logger.error(f"type_field failed: {e}")
            return False

    def _get_verify_base_path(self) -> str:
        """Get the base path for verification templates.

        Resolves relative paths against bundle dir for frozen builds.

        Returns:
            Absolute base path like '/path/to/assets/verify'
        """
        raw_path = self.settings.get("validation", {}).get("verify_base_path", "assets/verify")
        base = Path(raw_path)
        if not base.is_absolute():
            base = paths.get_bundle_dir() / base
        return str(base)

    def _wait_and_verify(
        self,
        step: Dict[str, Any],
        verify_image: str,
        validation_cfg: Dict[str, Any]
    ) -> bool:
        """Wait for next screen and retry click if needed.

        Flow:
        1. Poll for expected screen header (timeout from config)
        2. If found -> success
        3. If timeout -> re-locate and retry click (max_retries)
        4. If max retries exhausted -> return False

        Args:
            step: The step definition (for retry click)
            verify_image: Relative image path like '1120S/06_s_corp_name.png'
            validation_cfg: Validation settings dict

        Returns:
            True if screen verified, False if all retries exhausted
        """
        timeout = step.get("verify_timeout", validation_cfg.get("step_timeout_s", 10.0))
        poll_interval = validation_cfg.get("poll_interval_ms", 333) / 1000
        no_retry = step.get("no_retry", False)
        max_retries = 1 if no_retry else validation_cfg.get("max_retries", 3)
        min_wait = validation_cfg.get("min_wait_after_ms", 200) / 1000
        verify_base = self._get_verify_base_path()
        step_name = step.get("name", "unknown")
        step_action = step.get("action", "unknown")
        confidence_threshold = self.settings.get("vision", {}).get(
            "confidence_threshold", 0.8
        )

        for retry in range(max_retries):
            # Check stop signal before each retry
            if self.stop_event.is_set():
                logger.info("  -> Verification aborted: stop signal")
                return False

            self._send_log(
                f"DEBUG verify: waiting for {verify_image} "
                f"(attempt {retry + 1}/{max_retries}, timeout={timeout}s)"
            )
            logger.info(
                f"  -> Verifying: {verify_base}/{verify_image} "
                f"(timeout={timeout}s, attempt {retry + 1}/{max_retries})"
            )
            coords = vision.wait_for_element(
                verify_image, timeout=timeout, poll_interval=poll_interval,
                base_path=verify_base, stop_event=self.stop_event
            )

            if coords is not None:
                logger.info(f"  -> Screen verified: {verify_image}")
                time.sleep(min_wait)
                return True

            # Stop signal may have caused the timeout
            if self.stop_event.is_set():
                logger.info("  -> Verification aborted: stop signal")
                return False

            # --- DEBUG: diagnose why verification failed ---
            try:
                max_conf, tmpl_loaded, full_path = vision.debug_match_confidence(
                    verify_image, base_path=verify_base
                )
                if not tmpl_loaded:
                    debug_msg = (
                        f"DEBUG verify FAIL: template NOT FOUND at {full_path}"
                    )
                else:
                    debug_msg = (
                        f"DEBUG verify FAIL: {verify_image} | "
                        f"confidence={max_conf:.4f} vs threshold={confidence_threshold} | "
                        f"path={full_path}"
                    )
                self._send_log(debug_msg)
                logger.warning(debug_msg)

                # Also check if the click target from this step is still visible
                target = step.get("target", {})
                target_image = target.get("image") if isinstance(target, dict) else None
                if target_image:
                    target_conf, target_loaded, target_path = vision.debug_match_confidence(
                        target_image
                    )
                    if target_loaded:
                        target_msg = (
                            f"DEBUG click target: {target_image} | "
                            f"confidence={target_conf:.4f} (still on screen?)"
                        )
                    else:
                        target_msg = (
                            f"DEBUG click target: {target_image} NOT FOUND at {target_path}"
                        )
                    self._send_log(target_msg)
                    logger.warning(target_msg)
            except Exception as e:
                self._send_log(f"DEBUG EXCEPTION: {type(e).__name__}: {e}")
                logger.error(f"Debug match failed: {e}", exc_info=True)

            # Timeout: retry the click (unless no_retry is set)
            if retry < max_retries - 1:
                if step_action in ("multi", "conditional", "scroll", "scroll_until_visible"):
                    skip_msg = (
                        f"DEBUG retry: action='{step_action}' -> "
                        f"retry click SKIPPED (not supported for {step_action})"
                    )
                    logger.warning(skip_msg)
                    self._send_log(skip_msg)
                else:
                    logger.warning(f"  -> Screen not verified, retrying click...")
                self._send_log(f"Retry {retry + 1}: {step_name}")
                self._retry_step_click(step)

        logger.error(f"  -> Verification FAILED after {max_retries} attempts")
        return False

    def _retry_step_click(self, step: Dict[str, Any]) -> None:
        """Re-execute the click action of a step for retry.

        Args:
            step: Step definition dict
        """
        action = step.get("action")
        target = step.get("target", {})

        if action == "click":
            self._action_click(target)
        elif action == "double_click":
            self._action_double_click(target)
        # For conditional/scroll/multi: don't retry click, just wait longer

    def _action_multi(self, step: Dict[str, Any], static_inputs: Dict[str, str]) -> bool:
        """Execute multiple sub-actions in sequence.

        Used for consolidated stages (e.g., select checkbox + click continue).

        Args:
            step: Step definition containing 'actions' list
            static_inputs: Static input values

        Returns:
            True if all sub-actions succeeded
        """
        sub_actions = step.get("actions", [])
        for i, sub in enumerate(sub_actions):
            logger.debug(f"  -> Multi sub-action {i + 1}/{len(sub_actions)}: {sub.get('action')}")
            if not self._execute_step(sub, static_inputs):
                return False
            sub_wait = sub.get("wait_after", 0.5)
            if sub_wait > 0:
                time.sleep(sub_wait)
        return True

    # --- Message Helpers ---

    def _send_status(self, message: str) -> None:
        """Send status update to GUI."""
        self.message_queue.put(StatusMessage("status", message))

    def _send_log(self, message: str) -> None:
        """Send log message to GUI."""
        self.message_queue.put(StatusMessage("log", message))

    def _send_error(self, message: str) -> None:
        """Send error message to GUI."""
        self.message_queue.put(StatusMessage("error", message))
