"""Bot controller for managing automation in a separate thread.

Provides thread-safe communication between GUI and bot logic via message queue.
"""

import logging
import queue
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import pydirectinput
import pyautogui

from clickbot import sounds
from clickbot import window_validator
from clickbot import vision
from clickbot import executor

logger = logging.getLogger(__name__)


class BotState(Enum):
    """Bot state enumeration."""
    IDLE = "idle"
    COUNTDOWN = "countdown"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"


@dataclass
class StatusMessage:
    """Message for GUI updates."""
    type: str  # "status", "log", "error", "complete", "countdown"
    message: str
    data: Optional[dict] = None


class BotController:
    """Controls bot execution in a separate thread.

    Provides thread-safe communication via message queue.
    The GUI polls get_messages() to receive updates.
    """

    def __init__(
        self,
        settings: dict,
        selected_return_type: str = "1120S",
        csv_path: Optional[Path] = None
    ):
        """Initialize the bot controller.

        Args:
            settings: Settings dict from config/settings.json
            selected_return_type: Return type chosen by user in GUI (e.g. "1120", "1120S", "1040")
            csv_path: Optional path to CSV file for persistent client tracking
        """
        self.settings = settings
        self.selected_return_type = selected_return_type
        self.csv_path = csv_path
        self.state = BotState.IDLE
        self.message_queue: queue.Queue[StatusMessage] = queue.Queue()
        self.stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        logger.debug(f"BotController initialized (return_type={selected_return_type})")

    def validate_taxact(self) -> tuple[bool, str]:
        """Validate TaxAct is ready for automation.

        Returns:
            Tuple of (success, message)
        """
        return window_validator.validate_startup(self.settings)

    def start(self) -> bool:
        """Start the bot in a new thread.

        Returns:
            True if started successfully, False otherwise
        """
        if self.state != BotState.IDLE:
            logger.warning(f"Cannot start: bot is in state {self.state}")
            return False

        self.stop_event.clear()
        self.state = BotState.RUNNING

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

        logger.info("Bot thread started")
        return True

    def stop(self) -> None:
        """Signal the bot to stop."""
        logger.info("Stop signal received")
        self.stop_event.set()
        self.state = BotState.STOPPING

        # Wait for thread to finish (max 2 seconds)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self.state = BotState.IDLE
        logger.info("Bot stopped")

    def get_state(self) -> BotState:
        """Get current bot state.

        Returns:
            Current BotState
        """
        return self.state

    def get_messages(self) -> list[StatusMessage]:
        """Get all pending messages from queue.

        Returns:
            List of StatusMessage objects
        """
        messages = []
        try:
            while True:
                msg = self.message_queue.get_nowait()
                messages.append(msg)
        except queue.Empty:
            pass
        return messages

    def _recover_to_client_manager(self) -> None:
        """Navigate back to Client Manager after a process error.

        Clicks the 'Clients' button in the top menu bar to return to base state,
        then scrolls the client table to the top via Ctrl+Home.
        """
        self._send_status("Recovering: returning to Client Manager...")
        self._send_log("Clicking 'Clients' to return to base...")

        try:
            clicked = vision.find_and_click(
                "common/clients_button.png",
                wait_after=3.0
            )
            if clicked:
                logger.info("Recovery: clicked Clients button, back to Client Manager")
                self._send_log("Recovery successful")
            else:
                logger.error("Recovery: Clients button not found")
                self._send_error("Recovery failed: Clients button not found")
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            self._send_error(f"Recovery failed: {e}")

        # Scroll client table to top so next scan starts from the beginning
        self._scroll_table_to_top()

    def _scroll_table_to_top(self) -> None:
        """Click into the client table and press Ctrl+Home to scroll to top."""
        scroll_top = self.settings.get("loop", {}).get("scroll_to_top", {})
        if scroll_top.get("enabled", True):
            focus_x = scroll_top.get("focus_click_x", 200)
            focus_y = scroll_top.get("focus_click_y", 300)
            pyautogui.click(focus_x, focus_y)
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'home')
            time.sleep(scroll_top.get("delay_s", 0.3))
            logger.debug("Scrolled client table to top")

    def _send_status(self, message: str) -> None:
        """Send status update to GUI."""
        self.message_queue.put(StatusMessage("status", message))

    def _send_log(self, message: str) -> None:
        """Send log message to GUI."""
        self.message_queue.put(StatusMessage("log", message))

    def _send_progress(self, message: str) -> None:
        """Send progress update to GUI."""
        self.message_queue.put(StatusMessage("progress", message))

    def _send_complete(self, message: str) -> None:
        """Send completion message to GUI."""
        self.message_queue.put(StatusMessage("complete", message))

    def _send_error(self, message: str) -> None:
        """Send error message to GUI."""
        self.message_queue.put(StatusMessage("error", message))

    def _run(self) -> None:
        """Main bot loop - runs in worker thread.

        Processes clients in a loop until:
        - No more unprocessed clients found
        - Stop signal received

        When csv_path is set, uses CSV for client tracking (composite-key lookup,
        post-iteration status writes). Otherwise falls back to in-memory tracking.

        WARNING: Do NOT update any UI elements from this method!
        Use self.message_queue.put() to send updates to GUI.
        """
        from clickbot.process_executor import ProcessExecutor
        from clickbot.state import ClientTracker

        logger.info("Bot worker thread running")
        self._send_status("Bot running")

        # Configure vision module
        vision.configure(self.settings)
        vision.configure_tesseract(self.settings)

        # Initialize tracking: CSV (persistent) or in-memory (fallback)
        csv_records = None
        if self.csv_path and self.csv_path.exists():
            from clickbot.preprocessor import load_csv, update_client_status
            csv_records = load_csv(self.csv_path)
            todo_count = sum(
                1 for r in csv_records
                if r.return_type == self.selected_return_type and r.status == "TODO"
            )
            self._send_log(f"CSV loaded: {todo_count} TODO clients for {self.selected_return_type}")

        tracker = ClientTracker()
        clients_processed = 0
        start_time = time.time()

        # Main processing loop
        while not self.stop_event.is_set():
            # Play iteration sound (except first iteration)
            if clients_processed > 0:
                sounds.play_iteration()

            # Scroll client list to top via Ctrl+Home
            self._scroll_table_to_top()

            # Find next unprocessed client
            self._send_status("Scanning client table...")
            self._send_log("Looking for unprocessed client...")

            if csv_records is not None:
                # CSV mode: scan page by page with screenshot-crop approach
                preprocessing_cfg = self.settings.get("preprocessing", {})
                refocus_x = preprocessing_cfg.get("refocus_click_x", 200)
                refocus_y = preprocessing_cfg.get("refocus_click_y", 1065)
                post_scroll_delay = preprocessing_cfg.get("post_scroll_delay_s", 0.5)
                max_scroll = self.settings.get("loop", {}).get(
                    "scroll_in_table", {}
                ).get("max_attempts", 20)

                client_result = None
                last_seen_client = ""
                stale_count = 0

                for scroll_attempt in range(max_scroll + 1):
                    if self.stop_event.is_set():
                        break

                    screenshot = pyautogui.screenshot()
                    row_data, click_pos, last_client = vision.scan_visible_clients_csv(
                        screenshot, self.settings, csv_records,
                        self.selected_return_type, self.stop_event,
                    )

                    if row_data is not None:
                        client_result = (row_data, click_pos)
                        break

                    # End-of-table detection (like preprocessor.py stale_count)
                    if last_client == last_seen_client:
                        stale_count += 1
                        if stale_count >= 3:
                            logger.info(
                                f"End of table: last client '{last_client}' "
                                f"unchanged after {stale_count} attempts"
                            )
                            break
                    else:
                        stale_count = 0
                    last_seen_client = last_client

                    # Scroll: refocus click + arrow down (like preprocessor)
                    if scroll_attempt < max_scroll:
                        logger.debug(
                            f"No TODO on page, scrolling "
                            f"(attempt {scroll_attempt + 1}/{max_scroll})"
                        )
                        pyautogui.click(refocus_x, refocus_y)
                        self.stop_event.wait(0.2)
                        pydirectinput.press('down')
                        self.stop_event.wait(post_scroll_delay)
            else:
                client_result = vision.find_next_client(
                    self.settings,
                    selected_return_type=self.selected_return_type,
                    processed_clients=tracker.processed
                )

            if client_result is None:
                # No more clients to process
                elapsed = time.time() - start_time
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                self._send_complete(f"All done! Processed {clients_processed} clients in {minutes}m {seconds}s")
                self._send_log(f"No more unprocessed clients found")
                sounds.play_complete()
                break

            # Check for stop signal
            if self.stop_event.is_set():
                break

            client_row, click_pos = client_result

            # Mark as processed (in-memory fallback only)
            if csv_records is None:
                tracker.mark_processed(client_row.client_name)
            clients_processed += 1

            # Update progress
            self._send_progress(f"Processing client {clients_processed}")
            self._send_log(f"Selected: {client_row.client_name} ({client_row.return_type})")
            self._send_status(f"Opening: {client_row.client_name}")

            # Double-click to open the client
            logger.info(f"{'='*60}")
            logger.info(f"CLIENT #{clients_processed}: {client_row.client_name} ({client_row.return_type})")
            logger.info(f"{'='*60}")
            executor.double_click(click_pos[0], click_pos[1], wait=4.0)

            # Check for locked client dialog after double-click
            locked = vision.find_element(
                "common/locked_1.png", retry_count=1,
                region=(800, 580, 300, 40)
            )
            if locked is not None:
                self._send_log("Client is locked, dismissing dialog...")
                vision.find_and_click("common/ok_default.png", wait_after=2.0)

            # Check for stop signal
            if self.stop_event.is_set():
                break

            # Execute the process for this client
            self._send_status(f"Processing: {client_row.client_name}")

            process_executor = ProcessExecutor(
                self.settings,
                self.message_queue,
                self.stop_event
            )

            result = process_executor.execute(self.selected_return_type)

            if result.success:
                # Update CSV status to "Submitted"
                if csv_records is not None:
                    update_client_status(
                        self.csv_path, client_row.client_name,
                        client_row.client_id, self.selected_return_type, "Submitted"
                    )
                    csv_records = load_csv(self.csv_path)
                self._send_log(f"Completed: {client_row.client_name} ({result.steps_completed}/{result.total_steps} steps)")
            else:
                if result.error_message == "Stopped by user":
                    break
                # Update CSV with specific failure reason
                if csv_records is not None:
                    if result.abort_reason:
                        csv_status = result.abort_reason
                    else:
                        csv_status = f"FAIL: {result.error_message or 'Unknown error'}"
                    update_client_status(
                        self.csv_path, client_row.client_name,
                        client_row.client_id, self.selected_return_type, csv_status
                    )
                    csv_records = load_csv(self.csv_path)
                # Error occurred - navigate back to Client Manager before continuing
                self._send_log(f"SKIPPED: {client_row.client_name} - {result.abort_reason or result.error_message}")
                sounds.play_error()
                self._recover_to_client_manager()

        self.state = BotState.IDLE
        logger.info(f"Bot worker thread finished (processed {clients_processed} clients)")
