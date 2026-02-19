"""Bot controller for managing automation in a separate thread.

Provides thread-safe communication between GUI and bot logic via message queue.
"""

import logging
import queue
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

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

    def __init__(self, settings: dict):
        """Initialize the bot controller.

        Args:
            settings: Settings dict from config/settings.json
        """
        self.settings = settings
        self.state = BotState.IDLE
        self.message_queue: queue.Queue[StatusMessage] = queue.Queue()
        self.stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        logger.debug("BotController initialized")

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

        Clicks the 'Clients' button in the top menu bar to return to base state.
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

        # Initialize state tracking
        tracker = ClientTracker()
        clients_processed = 0
        start_time = time.time()

        # Main processing loop
        while not self.stop_event.is_set():
            # Play iteration sound (except first iteration)
            if clients_processed > 0:
                sounds.play_iteration()

            # Find next unprocessed client
            self._send_status("Scanning client table...")
            self._send_log("Looking for unprocessed client...")

            client_result = vision.find_next_client(
                self.settings,
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

            # Mark as processed BEFORE starting (prevents retry on failure)
            tracker.mark_processed(client_row.client_name)
            clients_processed += 1

            # Update progress
            self._send_progress(f"Processing client {clients_processed}")
            self._send_log(f"Selected: {client_row.client_name} ({client_row.return_type})")
            self._send_status(f"Opening: {client_row.client_name}")

            # Double-click to open the client
            logger.info(f"Double-clicking client at ({click_pos[0]}, {click_pos[1]})")
            executor.double_click(click_pos[0], click_pos[1], wait=4.0)

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

            result = process_executor.execute(client_row.return_type)

            if result.success:
                self._send_log(f"Completed: {client_row.client_name} ({result.steps_completed}/{result.total_steps} steps)")
            else:
                if result.error_message == "Stopped by user":
                    break
                # Error occurred - navigate back to Client Manager before continuing
                self._send_log(f"SKIPPED: {client_row.client_name} - {result.error_message}")
                sounds.play_error()
                self._recover_to_client_manager()

        self.state = BotState.IDLE
        logger.info(f"Bot worker thread finished (processed {clients_processed} clients)")
