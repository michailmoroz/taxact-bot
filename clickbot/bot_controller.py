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

    def _run(self) -> None:
        """Main bot loop - runs in worker thread.

        WARNING: Do NOT update any UI elements from this method!
        Use self.message_queue.put() to send updates to GUI.
        """
        from clickbot.process_executor import ProcessExecutor

        logger.info("Bot worker thread running")
        self.message_queue.put(StatusMessage("status", "Bot running"))

        # Configure vision module
        vision.configure(self.settings)
        vision.configure_tesseract(self.settings)

        # Step 1: Find next unprocessed client in the table
        self.message_queue.put(StatusMessage("status", "Scanning client table..."))
        self.message_queue.put(StatusMessage("log", "Looking for unprocessed 1120 client..."))

        target_return_type = "1120"
        client_result = vision.find_next_client(self.settings, target_return_type)

        if client_result is None:
            self.message_queue.put(StatusMessage("complete", "No unprocessed clients found"))
            self.message_queue.put(StatusMessage("log", f"No clients with empty Fed EF Status and type {target_return_type}"))
            sounds.play_complete()
            self.state = BotState.IDLE
            return

        # Check for stop signal
        if self.stop_event.is_set():
            self.state = BotState.IDLE
            return

        client_row, click_pos = client_result
        self.message_queue.put(StatusMessage("log", f"Selected: {client_row.client_name} ({client_row.return_type})"))
        self.message_queue.put(StatusMessage("status", f"Opening: {client_row.client_name}"))

        # Step 2: Double-click to open the client
        logger.info(f"Double-clicking client at ({click_pos[0]}, {click_pos[1]})")
        executor.double_click(click_pos[0], click_pos[1], wait=3.0)

        # Check for stop signal
        if self.stop_event.is_set():
            self.state = BotState.IDLE
            return

        # Step 3: Execute the process for this client
        self.message_queue.put(StatusMessage("status", f"Processing: {client_row.client_name}"))

        process_executor = ProcessExecutor(
            self.settings,
            self.message_queue,
            self.stop_event
        )

        result = process_executor.execute(target_return_type)

        if result.success:
            self.message_queue.put(StatusMessage("complete",
                f"Completed {client_row.client_name}! {result.steps_completed}/{result.total_steps} steps"))
            sounds.play_complete()
        else:
            if result.error_message != "Stopped by user":
                self.message_queue.put(StatusMessage("error", result.error_message or "Unknown error"))
                sounds.play_error()

        self.state = BotState.IDLE
        logger.info("Bot worker thread finished")
