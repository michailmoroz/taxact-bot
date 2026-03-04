"""Modern GUI for TaxAct E-File Extension Bot using CustomTkinter.

Provides a user-friendly desktop interface with:
- Start button with 5-second countdown
- Stop button for immediate abort
- Real-time status display
- Scrollable log area
"""

import logging
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from clickbot import paths
from clickbot import sounds
from clickbot import window_validator
from clickbot.bot_controller import BotController, BotState, StatusMessage

logger = logging.getLogger(__name__)


class GUIState(Enum):
    """GUI state enumeration."""
    READY = "ready"
    COUNTDOWN = "countdown"
    RUNNING = "running"


class BotGUI(ctk.CTk):
    """Main GUI window for the TaxAct E-File Extension Bot."""

    def __init__(self, settings: dict):
        """Initialize the GUI.

        Args:
            settings: Settings dict from config/settings.json
        """
        # Set appearance BEFORE super().__init__()
        gui_settings = settings.get("gui", {})
        ctk.set_appearance_mode(gui_settings.get("appearance_mode", "dark"))
        ctk.set_default_color_theme(gui_settings.get("color_theme", "blue"))

        super().__init__()

        self.settings = settings
        self.gui_state = GUIState.READY
        self.controller: Optional[BotController] = None

        # Timer IDs for cancellation
        self._countdown_id: Optional[str] = None
        self._polling_id: Optional[str] = None
        self._countdown_value = 0

        self._setup_window()
        self._create_widgets()
        self._setup_layout()

        # Initial log entry
        self._log("Application started")
        logger.info("GUI initialized")

    def _setup_window(self) -> None:
        """Configure main window properties."""
        gui_settings = self.settings.get("gui", {})

        self.title("TaxAct E-File Extension Bot")
        self.geometry(f"{gui_settings.get('window_width', 500)}x{gui_settings.get('window_height', 650)}")
        self.minsize(400, 550)

        # Configure grid weights for responsive layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)  # Log area expands

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        # Header Frame
        self.header_frame = ctk.CTkFrame(self)
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="TaxAct E-File Extension Bot",
            font=ctk.CTkFont(size=20, weight="bold")
        )

        # Return Type Frame
        self.return_type_frame = ctk.CTkFrame(self)
        self.return_type_label = ctk.CTkLabel(
            self.return_type_frame,
            text="Return Type:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.return_type_selector = ctk.CTkSegmentedButton(
            self.return_type_frame,
            values=["1120", "1120S", "1040"],
            font=ctk.CTkFont(size=13)
        )
        self.return_type_selector.set("1120S")

        # Control Frame (Start/Stop Button, Countdown)
        self.control_frame = ctk.CTkFrame(self)
        self.start_button = ctk.CTkButton(
            self.control_frame,
            text="Start Bot",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="green",
            hover_color="darkgreen",
            height=50,
            command=self._on_start_click
        )
        self.countdown_label = ctk.CTkLabel(
            self.control_frame,
            text="",
            font=ctk.CTkFont(size=48, weight="bold")
        )
        self.countdown_hint = ctk.CTkLabel(
            self.control_frame,
            text="Switch to TaxAct now!",
            font=ctk.CTkFont(size=14)
        )

        # Status Frame
        self.status_frame = ctk.CTkFrame(self)
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Status: Ready",
            font=ctk.CTkFont(size=14)
        )
        self.taxact_status_label = ctk.CTkLabel(
            self.status_frame,
            text="TaxAct: Checking...",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )

        # Log Frame
        self.log_frame = ctk.CTkFrame(self)
        self.log_label = ctk.CTkLabel(
            self.log_frame,
            text="Log:",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.log_textbox = ctk.CTkTextbox(
            self.log_frame,
            height=200,
            state="disabled",
            wrap="word"
        )

    def _setup_layout(self) -> None:
        """Arrange widgets using grid layout."""
        # Header
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.title_label.pack(pady=10)

        # Return Type Selector
        self.return_type_frame.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.return_type_label.pack(side="left", padx=(10, 8), pady=10)
        self.return_type_selector.pack(side="left", padx=(0, 10), pady=10)

        # Control
        self.control_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.start_button.pack(pady=20, padx=40, fill="x")
        # Countdown labels initially hidden

        # Status
        self.status_frame.grid(row=3, column=0, padx=20, pady=10, sticky="new")
        self.status_label.pack(anchor="w", padx=10, pady=(10, 5))
        self.taxact_status_label.pack(anchor="w", padx=10, pady=2)
        self.progress_label.pack(anchor="w", padx=10, pady=(2, 10))

        # Log
        self.log_frame.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        self.log_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")


    def _log(self, message: str) -> None:
        """Add a message to the log textbox.

        Args:
            message: Message to log
        """
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"> {message}\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")  # Scroll to bottom

    # --- State Machine ---

    def _on_start_click(self) -> None:
        """Handle start/stop button click."""
        if self.gui_state == GUIState.READY:
            self._start_countdown()
        elif self.gui_state == GUIState.COUNTDOWN:
            self._cancel_countdown()
        elif self.gui_state == GUIState.RUNNING:
            self._stop_bot()

    def _start_countdown(self) -> None:
        """Start the countdown sequence."""
        self.gui_state = GUIState.COUNTDOWN
        self._countdown_value = self.settings.get("gui", {}).get("countdown_seconds", 5)

        # Disable return type selector during countdown/running
        self.return_type_selector.configure(state="disabled")

        # Update button
        self.start_button.configure(
            text="Cancel",
            fg_color="orange",
            hover_color="darkorange"
        )

        # Show countdown
        self.start_button.pack_forget()
        self.countdown_label.pack(pady=10)
        self.countdown_hint.pack(pady=5)
        self.start_button.pack(pady=10, padx=40, fill="x")

        self._log(f"Countdown started ({self._countdown_value}s)")
        self._update_countdown()

    def _update_countdown(self) -> None:
        """Update countdown display."""
        if self._countdown_value > 0 and self.gui_state == GUIState.COUNTDOWN:
            self.countdown_label.configure(text=str(self._countdown_value))
            self._countdown_value -= 1
            self._countdown_id = self.after(1000, self._update_countdown)
        elif self.gui_state == GUIState.COUNTDOWN:
            self._finish_countdown()

    def _cancel_countdown(self) -> None:
        """Cancel the countdown and return to ready state."""
        if self._countdown_id:
            self.after_cancel(self._countdown_id)
            self._countdown_id = None

        self._log("Countdown cancelled")
        self._set_ready_state()

    def _finish_countdown(self) -> None:
        """Countdown finished, start the bot."""
        self.countdown_label.pack_forget()
        self.countdown_hint.pack_forget()
        self._set_running_state()
        self._start_bot()

    def _set_ready_state(self) -> None:
        """Set GUI to ready state."""
        self.gui_state = GUIState.READY
        self._countdown_value = 0

        # Hide countdown elements
        self.countdown_label.pack_forget()
        self.countdown_hint.pack_forget()

        # Re-enable return type selector
        self.return_type_selector.configure(state="normal")

        # Reset button
        self.start_button.pack_forget()
        self.start_button.configure(
            text="Start Bot",
            fg_color="green",
            hover_color="darkgreen"
        )
        self.start_button.pack(pady=20, padx=40, fill="x")

        self.status_label.configure(text="Status: Ready")

    def _set_running_state(self) -> None:
        """Set GUI to running state."""
        self.gui_state = GUIState.RUNNING
        self.start_button.configure(
            text="Stop",
            fg_color="red",
            hover_color="darkred"
        )

    # --- Bot Control ---

    def _start_bot(self) -> None:
        """Start the bot after countdown."""
        selected_return_type = self.return_type_selector.get()
        self.controller = BotController(self.settings, selected_return_type=selected_return_type)
        self._log(f"Return type selected: {selected_return_type}")

        # Validate TaxAct first
        success, message = self.controller.validate_taxact()
        if not success:
            self._log(f"ERROR: {message}")
            sounds.play_error()
            self._set_ready_state()
            return

        self._log("Bot started")
        self.status_label.configure(text="Status: Running...")
        sounds.play_success()

        # Start bot and polling
        self.controller.start()
        self._start_polling()

    def _stop_bot(self) -> None:
        """Stop the running bot."""
        if self.controller:
            self.controller.stop()
            self._log("Bot stopped")

        self._stop_polling()
        self._set_ready_state()

    def _start_polling(self) -> None:
        """Start polling for controller messages."""
        self._poll_messages()

    def _stop_polling(self) -> None:
        """Stop polling for messages."""
        if self._polling_id:
            self.after_cancel(self._polling_id)
            self._polling_id = None

    def _poll_messages(self) -> None:
        """Poll message queue and update UI."""
        if self.controller:
            messages = self.controller.get_messages()
            for msg in messages:
                self._handle_message(msg)

            # Check if bot is still running
            if self.controller.get_state() == BotState.IDLE:
                self._set_ready_state()
            else:
                self._polling_id = self.after(100, self._poll_messages)

    def _handle_message(self, msg: StatusMessage) -> None:
        """Handle a message from the controller.

        Args:
            msg: StatusMessage to handle
        """
        if msg.type == "log":
            self._log(msg.message)
        elif msg.type == "status":
            self.status_label.configure(text=f"Status: {msg.message}")
        elif msg.type == "progress":
            self.progress_label.configure(text=msg.message)
        elif msg.type == "error":
            self._log(f"ERROR: {msg.message}")
            # Note: Don't play error sound here - bot_controller already plays it
        elif msg.type == "complete":
            self._log(msg.message)
            self.status_label.configure(text="Status: Complete!")
            self.progress_label.configure(text="")

    # --- Lifecycle ---

    def _on_close(self) -> None:
        """Handle window close event."""
        logger.info("Window close requested")

        if self.controller and self.controller.get_state() != BotState.IDLE:
            self.controller.stop()

        self._stop_polling()

        if self._countdown_id:
            self.after_cancel(self._countdown_id)

        self.destroy()

    def check_taxact_on_startup(self) -> None:
        """Check TaxAct status on startup."""
        # Check if validation is skipped
        if self.settings.get("skip_taxact_validation", False):
            self.taxact_status_label.configure(
                text="TaxAct: Validation skipped (Dev)",
                text_color="orange"
            )
            self._log("TaxAct validation skipped (skip_taxact_validation=true)")
            return

        window = window_validator.find_taxact_window(
            self.settings.get("display", {}).get("taxact_window_title", "TaxAct")
        )

        if window:
            self.taxact_status_label.configure(
                text="TaxAct: Found",
                text_color="green"
            )
            self._log("TaxAct 2025 detected")
        else:
            self.taxact_status_label.configure(
                text="TaxAct: Not found",
                text_color="red"
            )
            self._log("WARNING: TaxAct not found - please open it")


def main() -> None:
    """Main entry point for GUI application."""
    from clickbot.main import load_settings, setup_logging

    # Load settings (copies default to %APPDATA% on first run when frozen)
    settings_path = paths.ensure_user_config()
    try:
        settings = load_settings(settings_path)
    except FileNotFoundError:
        print(f"ERROR: Settings file not found: {settings_path}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load settings: {e}")
        sys.exit(1)

    # Setup logging
    setup_logging(settings.get("dev_mode", False))

    # Create and run GUI
    logger.info("Starting GUI application")
    app = BotGUI(settings)

    # Initial TaxAct check (after 500ms to let window render)
    app.after(500, app.check_taxact_on_startup)

    app.mainloop()
    logger.info("GUI application closed")


if __name__ == "__main__":
    main()
