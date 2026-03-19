"""Modern GUI for TaxAct E-File Extension Bot using CustomTkinter.

Provides a user-friendly desktop interface with:
- Preprocessing button to scan client table and export CSV
- File picker for CSV selection
- Start button with 5-second countdown
- Stop button for immediate abort
- Real-time status display
- Scrollable log area
"""

import logging
import queue
import sys
import threading
from enum import Enum
from pathlib import Path
from tkinter import filedialog
from typing import Optional

import customtkinter as ctk

from clickbot import paths
from clickbot import sounds
from clickbot import window_validator
from clickbot.bot_controller import BotController, BotState, StatusMessage

logger = logging.getLogger(__name__)


# --- Design Tokens ---

COLORS = {
    "bg_primary":     "#1a1a1a",
    "bg_card":        "#242424",
    "bg_input":       "#2e2e2e",
    "border_subtle":  "#2e2e2e",
    "text_primary":   "#e5e5e5",
    "text_secondary": "#999999",
    "text_muted":     "#666666",
    "accent":         "#2563eb",
    "accent_hover":   "#1d4ed8",
    "success":        "#22c55e",
    "success_hover":  "#16a34a",
    "warning":        "#f59e0b",
    "warning_hover":  "#d97706",
    "error":          "#ef4444",
    "error_hover":    "#dc2626",
}

FONTS = {
    "title":     ("Segoe UI Semibold", 18),
    "section":   ("Segoe UI", 12),
    "selector":  ("Segoe UI Semibold", 15),
    "button":    ("Segoe UI Semibold", 15),
    "body":      ("Segoe UI", 13),
    "caption":   ("Segoe UI", 12),
    "countdown": ("Segoe UI", 48),
    "log":       ("Consolas", 12),
}


class GUIState(Enum):
    """GUI state enumeration."""
    READY = "ready"
    PREPROCESSING_COUNTDOWN = "preprocessing_countdown"
    PREPROCESSING = "preprocessing"
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

        # Preprocessing state
        self._csv_path: Optional[Path] = None
        self._preprocessing_queue: Optional[queue.Queue] = None
        self._preprocessing_stop: Optional[threading.Event] = None
        self._preprocessing_thread: Optional[threading.Thread] = None

        # Timer IDs for cancellation
        self._countdown_id: Optional[str] = None
        self._polling_id: Optional[str] = None
        self._countdown_value = 0

        self._setup_window()
        self._create_widgets()
        self._setup_layout()

        # Try to load latest CSV on startup
        self._load_latest_csv()

        # Initial log entry
        self._log("Application started")
        logger.info("GUI initialized")

    def _setup_window(self) -> None:
        """Configure main window properties."""
        gui_settings = self.settings.get("gui", {})

        self.title("TaxAct E-File Extension Bot")
        self.geometry(
            f"{gui_settings.get('window_width', 500)}"
            f"x{gui_settings.get('window_height', 820)}"
        )
        self.minsize(420, 680)
        self.configure(fg_color=COLORS["bg_primary"])

        # Configure grid weights for responsive layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)  # Log area expands (Row 5)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        # --- Header (compact, no frame) ---
        self.title_label = ctk.CTkLabel(
            self,
            text="TaxAct E-File Extension Bot",
            font=ctk.CTkFont(family=FONTS["title"][0], size=FONTS["title"][1]),
            text_color=COLORS["text_primary"],
            anchor="w",
        )

        # --- Return Type Hero Card ---
        self.return_type_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border_subtle"],
        )
        self.return_type_label = ctk.CTkLabel(
            self.return_type_frame,
            text="SELECT RETURN TYPE",
            font=ctk.CTkFont(family=FONTS["section"][0], size=FONTS["section"][1]),
            text_color=COLORS["text_secondary"],
        )
        self.return_type_selector = ctk.CTkSegmentedButton(
            self.return_type_frame,
            values=["1120", "1120S", "1040"],
            font=ctk.CTkFont(
                family=FONTS["selector"][0], size=FONTS["selector"][1]
            ),
            height=42,
            corner_radius=8,
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["bg_input"],
            unselected_hover_color="#3a3a3a",
            text_color=COLORS["text_primary"],
        )
        self.return_type_selector.set("1120S")

        # --- Preprocessing Card ---
        self.preprocessing_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border_subtle"],
        )
        self.preprocessing_button = ctk.CTkButton(
            self.preprocessing_frame,
            text="Scan Client Table",
            font=ctk.CTkFont(
                family=FONTS["button"][0], size=FONTS["button"][1]
            ),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text_primary"],
            height=48,
            corner_radius=8,
            command=self._on_preprocessing_click,
        )
        # CSV file picker row
        self.csv_file_frame = ctk.CTkFrame(
            self.preprocessing_frame,
            fg_color="transparent",
        )
        self.csv_path_label = ctk.CTkLabel(
            self.csv_file_frame,
            text="No CSV loaded",
            font=ctk.CTkFont(family=FONTS["caption"][0], size=FONTS["caption"][1]),
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        self.csv_browse_button = ctk.CTkButton(
            self.csv_file_frame,
            text="Browse",
            font=ctk.CTkFont(family=FONTS["caption"][0], size=FONTS["caption"][1]),
            fg_color=COLORS["bg_input"],
            hover_color="#3a3a3a",
            text_color=COLORS["text_secondary"],
            width=70,
            height=28,
            corner_radius=6,
            command=self._on_browse_csv,
        )
        self.csv_status_label = ctk.CTkLabel(
            self.preprocessing_frame,
            text="",
            font=ctk.CTkFont(family=FONTS["caption"][0], size=FONTS["caption"][1]),
            text_color=COLORS["text_secondary"],
        )
        # Preprocessing countdown labels (initially hidden)
        self.preproc_countdown_label = ctk.CTkLabel(
            self.preprocessing_frame,
            text="",
            font=ctk.CTkFont(
                family=FONTS["countdown"][0], size=FONTS["countdown"][1],
                weight="bold"
            ),
            text_color=COLORS["text_primary"],
        )
        self.preproc_countdown_hint = ctk.CTkLabel(
            self.preprocessing_frame,
            text="Switch to TaxAct now!",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS["text_secondary"],
        )

        # --- Control Card (Start/Stop Button, Countdown) ---
        self.control_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border_subtle"],
        )
        self.start_button = ctk.CTkButton(
            self.control_frame,
            text="Start Bot",
            font=ctk.CTkFont(
                family=FONTS["button"][0], size=FONTS["button"][1]
            ),
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            text_color=COLORS["text_primary"],
            height=48,
            corner_radius=8,
            command=self._on_start_click,
        )
        self.countdown_label = ctk.CTkLabel(
            self.control_frame,
            text="",
            font=ctk.CTkFont(
                family=FONTS["countdown"][0], size=FONTS["countdown"][1],
                weight="bold"
            ),
            text_color=COLORS["text_primary"],
        )
        self.countdown_hint = ctk.CTkLabel(
            self.control_frame,
            text="Switch to TaxAct now!",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS["text_secondary"],
        )

        # --- Status Card ---
        self.status_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border_subtle"],
        )
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Status: Ready",
            font=ctk.CTkFont(family=FONTS["body"][0], size=FONTS["body"][1]),
            text_color=COLORS["text_primary"],
        )
        self.taxact_status_label = ctk.CTkLabel(
            self.status_frame,
            text="TaxAct: Checking...",
            font=ctk.CTkFont(family=FONTS["caption"][0], size=FONTS["caption"][1]),
            text_color=COLORS["text_secondary"],
        )
        self.progress_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(family=FONTS["caption"][0], size=FONTS["caption"][1]),
            text_color=COLORS["text_secondary"],
        )

        # --- Log Card ---
        self.log_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border_subtle"],
        )
        self.log_label = ctk.CTkLabel(
            self.log_frame,
            text="Log:",
            font=ctk.CTkFont(family=FONTS["caption"][0], size=FONTS["caption"][1]),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.log_textbox = ctk.CTkTextbox(
            self.log_frame,
            height=200,
            state="disabled",
            wrap="word",
            font=ctk.CTkFont(family=FONTS["log"][0], size=FONTS["log"][1]),
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            corner_radius=6,
        )

    def _setup_layout(self) -> None:
        """Arrange widgets using grid layout."""
        pad_x = 24

        # Row 0 — Header (compact, left-aligned, no frame)
        self.title_label.grid(
            row=0, column=0, padx=pad_x, pady=(20, 4), sticky="w"
        )

        # Row 1 — Preprocessing Card
        self.preprocessing_frame.grid(
            row=1, column=0, padx=pad_x, pady=(8, 6), sticky="ew"
        )
        self.preprocessing_button.pack(pady=(16, 8), padx=16, fill="x")
        self.csv_file_frame.pack(padx=16, fill="x")
        self.csv_path_label.pack(side="left", expand=True, fill="x")
        self.csv_browse_button.pack(side="right", padx=(8, 0))
        self.csv_status_label.pack(padx=16, pady=(4, 12), anchor="w")

        # Row 2 — Return Type Hero Card
        self.return_type_frame.grid(
            row=2, column=0, padx=pad_x, pady=6, sticky="ew"
        )
        self.return_type_label.pack(padx=16, pady=(14, 4), anchor="center")
        self.return_type_selector.pack(padx=16, pady=(4, 14), fill="x")

        # Row 3 — Control Card
        self.control_frame.grid(
            row=3, column=0, padx=pad_x, pady=6, sticky="ew"
        )
        self.start_button.pack(pady=16, padx=16, fill="x")
        # Countdown labels initially hidden

        # Row 4 — Status Card
        self.status_frame.grid(
            row=4, column=0, padx=pad_x, pady=6, sticky="new"
        )
        self.status_label.pack(anchor="w", padx=16, pady=(12, 4))
        self.taxact_status_label.pack(anchor="w", padx=16, pady=2)
        self.progress_label.pack(anchor="w", padx=16, pady=(2, 12))

        # Row 5 — Log Card (expands vertically)
        self.log_frame.grid(
            row=5, column=0, padx=pad_x, pady=(6, 20), sticky="nsew"
        )
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_label.grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")
        self.log_textbox.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")


    def _log(self, message: str) -> None:
        """Add a message to the log textbox.

        Args:
            message: Message to log
        """
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"> {message}\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")  # Scroll to bottom

    # --- Preprocessing ---

    def _on_preprocessing_click(self) -> None:
        """Handle preprocessing button click — routes by current state."""
        if self.gui_state == GUIState.READY:
            self._start_preprocessing_countdown()
        elif self.gui_state == GUIState.PREPROCESSING_COUNTDOWN:
            self._cancel_preprocessing_countdown()
        elif self.gui_state == GUIState.PREPROCESSING:
            self._stop_preprocessing()

    def _start_preprocessing_countdown(self) -> None:
        """Start countdown before preprocessing scan."""
        self.gui_state = GUIState.PREPROCESSING_COUNTDOWN
        self._countdown_value = self.settings.get("gui", {}).get("countdown_seconds", 5)

        # Disable other controls
        self.start_button.configure(state="disabled")
        self.return_type_selector.configure(state="disabled")
        self.csv_browse_button.configure(state="disabled")

        # Show countdown in preprocessing card
        self.preprocessing_button.pack_forget()
        self.preproc_countdown_label.pack(pady=10)
        self.preproc_countdown_hint.pack(pady=5)
        self.preprocessing_button.configure(
            text="Cancel",
            fg_color=COLORS["warning"],
            hover_color=COLORS["warning_hover"],
        )
        self.preprocessing_button.pack(pady=(10, 8), padx=16, fill="x")

        self._log(f"Preprocessing countdown ({self._countdown_value}s)")
        self._update_preprocessing_countdown()

    def _update_preprocessing_countdown(self) -> None:
        """Tick the preprocessing countdown."""
        if self._countdown_value > 0 and self.gui_state == GUIState.PREPROCESSING_COUNTDOWN:
            self.preproc_countdown_label.configure(text=str(self._countdown_value))
            self._countdown_value -= 1
            self._countdown_id = self.after(1000, self._update_preprocessing_countdown)
        elif self.gui_state == GUIState.PREPROCESSING_COUNTDOWN:
            self._finish_preprocessing_countdown()

    def _cancel_preprocessing_countdown(self) -> None:
        """Cancel preprocessing countdown and return to ready."""
        if self._countdown_id:
            self.after_cancel(self._countdown_id)
            self._countdown_id = None

        self._log("Preprocessing countdown cancelled")
        self._reset_preprocessing_button()
        self._set_ready_state()

    def _finish_preprocessing_countdown(self) -> None:
        """Countdown done — hide countdown labels and start scanning."""
        self.preproc_countdown_label.pack_forget()
        self.preproc_countdown_hint.pack_forget()

        # Switch button to Stop
        self.preprocessing_button.pack_forget()
        self.preprocessing_button.configure(
            text="Stop Scan",
            fg_color=COLORS["error"],
            hover_color=COLORS["error_hover"],
        )
        self.preprocessing_button.pack(pady=(16, 8), padx=16, fill="x")

        self.gui_state = GUIState.PREPROCESSING
        self.status_label.configure(text="Status: Preprocessing...")

        # Setup message queue and stop event for preprocessing thread
        self._preprocessing_queue = queue.Queue()
        self._preprocessing_stop = threading.Event()

        from clickbot.preprocessor import preprocess_table

        self._preprocessing_thread = threading.Thread(
            target=preprocess_table,
            args=(self.settings, self._preprocessing_queue, self._preprocessing_stop),
            daemon=True,
        )
        self._preprocessing_thread.start()

        # Start polling for preprocessing messages
        self._poll_preprocessing()

    def _stop_preprocessing(self) -> None:
        """Stop a running preprocessing scan."""
        if self._preprocessing_stop is not None:
            self._preprocessing_stop.set()
        self._log("Preprocessing stopped by user")

    def _poll_preprocessing(self) -> None:
        """Poll preprocessing message queue."""
        if self._preprocessing_queue is None:
            return

        try:
            while True:
                msg = self._preprocessing_queue.get_nowait()
                self._handle_preprocessing_message(msg)
        except queue.Empty:
            pass

        # Check if thread is still running
        if (self._preprocessing_thread is not None
                and not self._preprocessing_thread.is_alive()):
            self._finish_preprocessing()
        else:
            self._polling_id = self.after(100, self._poll_preprocessing)

    def _handle_preprocessing_message(self, msg: StatusMessage) -> None:
        """Handle a message from the preprocessing thread."""
        if msg.type == "log":
            self._log(msg.message)
        elif msg.type == "status":
            self.status_label.configure(text=f"Status: {msg.message}")
        elif msg.type == "error":
            self._log(f"ERROR: {msg.message}")
        elif msg.type == "complete":
            # msg.message contains the CSV path on success
            csv_path = Path(msg.message)
            if csv_path.exists():
                self._load_csv_file(csv_path)

    def _finish_preprocessing(self) -> None:
        """Finish preprocessing and restore GUI state."""
        self._stop_polling()

        # Check if preprocessing produced a valid CSV
        if self._csv_path is not None:
            sounds.play_complete()
        else:
            sounds.play_error()

        self._reset_preprocessing_button()
        self._set_ready_state()

        # Cleanup
        self._preprocessing_queue = None
        self._preprocessing_stop = None
        self._preprocessing_thread = None

    def _reset_preprocessing_button(self) -> None:
        """Reset preprocessing button to default appearance and position."""
        self.preproc_countdown_label.pack_forget()
        self.preproc_countdown_hint.pack_forget()
        self.preprocessing_button.pack_forget()
        self.preprocessing_button.configure(
            text="Scan Client Table",
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            state="normal",
        )
        self.preprocessing_button.pack(pady=(16, 8), padx=16, fill="x")

    # --- CSV File Management ---

    def _on_browse_csv(self) -> None:
        """Open file dialog to select a CSV file."""
        csv_dir = self.settings.get("preprocessing", {}).get(
            "csv_output_dir", "C:/TaxActBot/logs"
        )
        filepath = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")],
            initialdir=csv_dir,
        )
        if filepath:
            self._load_csv_file(Path(filepath))

    def _load_csv_file(self, csv_path: Path) -> None:
        """Load a CSV file and update GUI labels.

        Args:
            csv_path: Path to the CSV file to load
        """
        from clickbot.preprocessor import load_csv

        try:
            records = load_csv(csv_path)
        except Exception as e:
            self._log(f"ERROR: Failed to load CSV: {e}")
            return

        self._csv_path = csv_path

        # Update path label (show only filename)
        self.csv_path_label.configure(
            text=f".../{csv_path.name}",
            text_color=COLORS["text_secondary"],
        )

        # Update status counts
        todo = sum(1 for r in records if r.status == "TODO")
        done = sum(1 for r in records if r.status == "DONE")
        fail = sum(1 for r in records if r.status == "FAIL")
        self.csv_status_label.configure(
            text=f"{todo} TODO, {done} DONE, {fail} FAIL"
        )

        self._log(f"CSV loaded: {csv_path.name} ({len(records)} clients)")
        logger.info(f"CSV loaded: {csv_path}")

    def _load_latest_csv(self) -> None:
        """Try to load the most recent CSV file on startup."""
        from clickbot.preprocessor import get_latest_csv

        csv_dir = Path(self.settings.get("preprocessing", {}).get(
            "csv_output_dir", "C:/TaxActBot/logs"
        ))
        latest = get_latest_csv(csv_dir)
        if latest is not None:
            self._load_csv_file(latest)

    # --- State Machine ---

    def _on_start_click(self) -> None:
        """Handle start/stop button click."""
        if self.gui_state == GUIState.READY:
            # Check CSV is loaded
            if self._csv_path is None:
                self._log("ERROR: No CSV file loaded. Run Preprocessing or load a CSV file.")
                return
            self._start_countdown()
        elif self.gui_state == GUIState.COUNTDOWN:
            self._cancel_countdown()
        elif self.gui_state == GUIState.RUNNING:
            self._stop_bot()

    def _start_countdown(self) -> None:
        """Start the countdown sequence."""
        self.gui_state = GUIState.COUNTDOWN
        self._countdown_value = self.settings.get("gui", {}).get("countdown_seconds", 5)

        # Disable controls during countdown/running
        self.return_type_selector.configure(state="disabled")
        self.preprocessing_button.configure(state="disabled")
        self.csv_browse_button.configure(state="disabled")

        # Update button
        self.start_button.configure(
            text="Cancel",
            fg_color=COLORS["warning"],
            hover_color=COLORS["warning_hover"],
        )

        # Show countdown
        self.start_button.pack_forget()
        self.countdown_label.pack(pady=10)
        self.countdown_hint.pack(pady=5)
        self.start_button.pack(pady=(10, 16), padx=16, fill="x")

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

        # Re-enable controls
        self.return_type_selector.configure(state="normal")
        self.preprocessing_button.configure(state="normal")
        self.csv_browse_button.configure(state="normal")

        # Reset button
        self.start_button.pack_forget()
        self.start_button.configure(
            text="Start Bot",
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
        )
        self.start_button.pack(pady=16, padx=16, fill="x")

        self.status_label.configure(text="Status: Ready")

    def _set_running_state(self) -> None:
        """Set GUI to running state."""
        self.gui_state = GUIState.RUNNING
        self.start_button.configure(
            text="Stop",
            fg_color=COLORS["error"],
            hover_color=COLORS["error_hover"],
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

        # Stop preprocessing if running
        if self._preprocessing_stop is not None:
            self._preprocessing_stop.set()

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
                text_color=COLORS["warning"],
            )
            self._log("TaxAct validation skipped (skip_taxact_validation=true)")
            return

        window = window_validator.find_taxact_window(
            self.settings.get("display", {}).get("taxact_window_title", "TaxAct")
        )

        if window:
            self.taxact_status_label.configure(
                text="TaxAct: Found",
                text_color=COLORS["success"],
            )
            self._log("TaxAct 2025 detected")
        else:
            self.taxact_status_label.configure(
                text="TaxAct: Not found",
                text_color=COLORS["error"],
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
