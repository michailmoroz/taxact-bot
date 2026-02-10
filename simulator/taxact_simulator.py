"""TaxAct Simulator - Mock GUI for testing the automation bot.

This application simulates TaxAct 2025 Professional at 1920x1080 resolution.
It uses the same button screenshots that the bot looks for, so the bot's
template matching will find the correct elements.

Usage:
    python -m simulator.taxact_simulator

The simulator will open fullscreen and display the Client Manager.
Click through screens or let the bot automate through them.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import customtkinter as ctk
from PIL import Image, ImageTk

from simulator.screens import SCREENS_1120, SCREENS_1120S, get_screens
from simulator.mock_data import MOCK_CLIENTS, MockClient

logger = logging.getLogger(__name__)

# Configure appearance
ctk.set_appearance_mode("light")  # TaxAct uses light theme


class TaxActSimulator(ctk.CTk):
    """TaxAct 2025 Professional Simulator.

    Provides a pixel-accurate simulation of TaxAct for testing
    the automation bot without real TaxAct access.
    """

    def __init__(self):
        super().__init__()

        # Window setup - match TaxAct exactly
        self.title("TaxAct 2025 Professional - [Simulator]")
        self.geometry("1920x1080")
        self.resizable(False, False)

        # State
        self.current_screen = "client_manager"
        self.current_return_type = "1120"
        self.screens = get_screens(self.current_return_type)
        self.selected_client: Optional[MockClient] = None
        self.textfield_values: Dict[str, str] = {}
        self.checkbox_states: Dict[str, bool] = {}
        self.alerts_passed = True  # Can be toggled for testing

        # Image cache
        self._image_cache: Dict[str, ctk.CTkImage] = {}

        # Screenshot base path
        self.img_base = Path(".agents/screenshots/buttons")

        # Setup
        self._setup_ui()
        self._render_screen()

        logger.info("TaxAct Simulator initialized")

    def _setup_ui(self):
        """Setup base UI structure."""
        # Main frame fills entire window
        self.main_frame = ctk.CTkFrame(self, fg_color="#f0f0f0", corner_radius=0)
        self.main_frame.pack(fill="both", expand=True)

        # Status bar at bottom
        self.status_frame = ctk.CTkFrame(self, height=30, fg_color="#e0e0e0")
        self.status_frame.pack(side="bottom", fill="x")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text=f"Screen: {self.current_screen} | Return Type: {self.current_return_type}",
            font=("Consolas", 12)
        )
        self.status_label.pack(side="left", padx=10)

        # Debug toggle
        self.debug_var = ctk.BooleanVar(value=True)
        self.debug_check = ctk.CTkCheckBox(
            self.status_frame,
            text="Show Debug Info",
            variable=self.debug_var,
            command=self._render_screen
        )
        self.debug_check.pack(side="right", padx=10)

        # Alerts toggle (for testing error path)
        self.alerts_var = ctk.BooleanVar(value=True)
        self.alerts_check = ctk.CTkCheckBox(
            self.status_frame,
            text="Alerts Pass",
            variable=self.alerts_var,
            command=self._on_alerts_toggle
        )
        self.alerts_check.pack(side="right", padx=10)

    def _on_alerts_toggle(self):
        """Handle alerts pass/fail toggle."""
        self.alerts_passed = self.alerts_var.get()
        if self.current_screen == "alerts_result":
            self._render_screen()

    def _clear_screen(self):
        """Clear all widgets from main frame."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def _load_image(self, image_path: str, size: tuple = None) -> Optional[ctk.CTkImage]:
        """Load image from path, with caching."""
        cache_key = f"{image_path}_{size}"

        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        full_path = self.img_base / image_path

        if not full_path.exists():
            logger.warning(f"Image not found: {full_path}")
            return None

        try:
            pil_image = Image.open(full_path)

            if size:
                pil_image = pil_image.resize(size, Image.Resampling.LANCZOS)

            ctk_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=pil_image.size
            )

            self._image_cache[cache_key] = ctk_image
            return ctk_image

        except Exception as e:
            logger.error(f"Failed to load image {full_path}: {e}")
            return None

    def _render_screen(self):
        """Render the current screen."""
        self._clear_screen()

        screen_def = self.screens.get(self.current_screen)
        if not screen_def:
            logger.error(f"Unknown screen: {self.current_screen}")
            return

        # Handle conditional screens
        if screen_def.get("conditional"):
            condition_var = screen_def.get("condition_var")
            if condition_var == "alerts_passed":
                elements = screen_def.get("elements_if_true" if self.alerts_passed else "elements_if_false", [])
            else:
                elements = screen_def.get("elements", [])
        else:
            elements = screen_def.get("elements", [])

        # Update status
        title = screen_def.get("title", self.current_screen)
        self.status_label.configure(
            text=f"Screen: {title} | Return Type: {self.current_return_type} | "
                 f"Client: {self.selected_client.name if self.selected_client else 'None'}"
        )

        # Render title
        if "title" in screen_def:
            title_label = ctk.CTkLabel(
                self.main_frame,
                text=screen_def["title"],
                font=("Segoe UI", 24, "bold"),
                text_color="#333333"
            )
            title_label.place(x=50, y=20)

        # Render elements
        for element in elements:
            self._render_element(element)

        # Show debug info
        if self.debug_var.get():
            self._render_debug_info(elements)

    def _render_element(self, element: Dict[str, Any]):
        """Render a single UI element."""
        elem_type = element.get("type")
        pos = element.get("position", (0, 0))

        if elem_type == "button":
            self._render_button(element, pos)
        elif elem_type == "checkbox":
            self._render_checkbox(element, pos)
        elif elem_type == "textfield":
            self._render_textfield(element)
        elif elem_type == "label":
            self._render_label(element, pos)
        elif elem_type == "image":
            self._render_image(element, pos)
        elif elem_type == "client_table":
            self._render_client_table(element, pos)

    def _render_button(self, element: Dict[str, Any], pos: tuple):
        """Render a button with image."""
        image_path = element.get("image")
        next_screen = element.get("next_screen")
        action = element.get("action")

        image = self._load_image(image_path)

        if image:
            btn = ctk.CTkButton(
                self.main_frame,
                image=image,
                text="",
                fg_color="transparent",
                hover_color="#e0e0e0",
                corner_radius=0,
                command=lambda: self._on_button_click(next_screen, action)
            )
            # Place at center of position
            btn.place(x=pos[0] - image._size[0]//2, y=pos[1] - image._size[1]//2)
        else:
            # Fallback text button
            btn = ctk.CTkButton(
                self.main_frame,
                text=f"[{image_path}]",
                command=lambda: self._on_button_click(next_screen, action)
            )
            btn.place(x=pos[0], y=pos[1])

    def _render_checkbox(self, element: Dict[str, Any], pos: tuple):
        """Render a checkbox with checked/unchecked images."""
        checked_img = element.get("image_checked")
        unchecked_img = element.get("image_unchecked")
        default_checked = element.get("checked", False)

        # Get or set state
        checkbox_id = f"{self.current_screen}_{pos}"
        if checkbox_id not in self.checkbox_states:
            self.checkbox_states[checkbox_id] = default_checked

        is_checked = self.checkbox_states[checkbox_id]
        image_path = checked_img if is_checked else unchecked_img
        image = self._load_image(image_path)

        if image:
            btn = ctk.CTkButton(
                self.main_frame,
                image=image,
                text="",
                fg_color="transparent",
                hover_color="#e0e0e0",
                corner_radius=0,
                command=lambda: self._toggle_checkbox(checkbox_id)
            )
            btn.place(x=pos[0] - image._size[0]//2, y=pos[1] - image._size[1]//2)

    def _toggle_checkbox(self, checkbox_id: str):
        """Toggle checkbox state and re-render."""
        self.checkbox_states[checkbox_id] = not self.checkbox_states.get(checkbox_id, False)
        self._render_screen()

    def _render_textfield(self, element: Dict[str, Any]):
        """Render a label + textfield combination."""
        label_img = element.get("label_image")
        label_pos = element.get("label_position", (0, 0))
        field_offset = element.get("field_offset", (150, 0))
        field_size = element.get("field_size", (200, 25))
        field_id = element.get("field_id", "unknown")

        # Render label image
        image = self._load_image(label_img)
        if image:
            label = ctk.CTkLabel(self.main_frame, image=image, text="")
            label.place(x=label_pos[0], y=label_pos[1])

        # Render textfield
        field_x = label_pos[0] + field_offset[0]
        field_y = label_pos[1] + field_offset[1]

        entry = ctk.CTkEntry(
            self.main_frame,
            width=field_size[0],
            height=field_size[1],
            font=("Segoe UI", 12)
        )
        entry.place(x=field_x, y=field_y)

        # Restore value if exists
        if field_id in self.textfield_values:
            entry.insert(0, self.textfield_values[field_id])

        # Save on change
        entry.bind("<KeyRelease>", lambda e: self._on_textfield_change(field_id, entry.get()))

    def _on_textfield_change(self, field_id: str, value: str):
        """Handle textfield value change."""
        self.textfield_values[field_id] = value

    def _render_label(self, element: Dict[str, Any], pos: tuple):
        """Render a text label."""
        text = element.get("text", "")
        font_size = element.get("font_size", 14)

        label = ctk.CTkLabel(
            self.main_frame,
            text=text,
            font=("Segoe UI", font_size),
            text_color="#333333"
        )
        label.place(x=pos[0], y=pos[1])

    def _render_image(self, element: Dict[str, Any], pos: tuple):
        """Render a static image."""
        image_path = element.get("image")
        image = self._load_image(image_path)

        if image:
            label = ctk.CTkLabel(self.main_frame, image=image, text="")
            label.place(x=pos[0] - image._size[0]//2, y=pos[1] - image._size[1]//2)

    def _render_client_table(self, element: Dict[str, Any], pos: tuple):
        """Render the client manager table."""
        row_height = element.get("row_height", 25)
        columns = element.get("columns", [])
        col_widths = element.get("column_widths", [100] * len(columns))

        # Header
        x = pos[0]
        for i, col in enumerate(columns):
            header = ctk.CTkLabel(
                self.main_frame,
                text=col,
                font=("Segoe UI", 12, "bold"),
                width=col_widths[i],
                anchor="w"
            )
            header.place(x=x, y=pos[1])
            x += col_widths[i] + 10

        # Rows
        y = pos[1] + row_height + 5
        for client in MOCK_CLIENTS:
            x = pos[0]

            # Client name (clickable)
            name_btn = ctk.CTkButton(
                self.main_frame,
                text=client.name,
                font=("Segoe UI", 11),
                width=col_widths[0],
                height=row_height,
                anchor="w",
                fg_color="transparent",
                text_color="#0066cc",
                hover_color="#e8f4fc",
                command=lambda c=client: self._on_client_double_click(c)
            )
            name_btn.place(x=x, y=y)
            x += col_widths[0] + 10

            # Return type
            type_label = ctk.CTkLabel(
                self.main_frame,
                text=client.return_type,
                font=("Segoe UI", 11),
                width=col_widths[1],
                anchor="w"
            )
            type_label.place(x=x, y=y)
            x += col_widths[1] + 10

            # Fed EF Status
            status_label = ctk.CTkLabel(
                self.main_frame,
                text=client.fed_ef_status or "(empty)",
                font=("Segoe UI", 11),
                width=col_widths[2],
                anchor="w",
                text_color="#666666" if not client.fed_ef_status else "#333333"
            )
            status_label.place(x=x, y=y)

            y += row_height + 2

    def _on_client_double_click(self, client: MockClient):
        """Handle double-click on client row."""
        logger.info(f"Client selected: {client.name} ({client.return_type})")
        self.selected_client = client
        self.current_return_type = client.return_type
        self.screens = get_screens(client.return_type)
        # Stay on client_manager - bot will click E-File menu
        self._render_screen()

    def _on_button_click(self, next_screen: Optional[str], action: Optional[str]):
        """Handle button click."""
        if action:
            logger.info(f"Action: {action}")
            # Handle special actions
            if action == "select_extension":
                pass  # Just visual feedback

        if next_screen:
            logger.info(f"Navigating to: {next_screen}")
            self.current_screen = next_screen
            self._render_screen()

    def _render_debug_info(self, elements: List[Dict[str, Any]]):
        """Render debug overlay showing element positions."""
        for element in elements:
            pos = element.get("position") or element.get("label_position")
            if pos:
                # Draw crosshair at position
                size = 10

                # Horizontal line
                h_line = ctk.CTkFrame(self.main_frame, width=size*2, height=1, fg_color="red")
                h_line.place(x=pos[0]-size, y=pos[1])

                # Vertical line
                v_line = ctk.CTkFrame(self.main_frame, width=1, height=size*2, fg_color="red")
                v_line.place(x=pos[0], y=pos[1]-size)

                # Position label
                pos_label = ctk.CTkLabel(
                    self.main_frame,
                    text=f"({pos[0]},{pos[1]})",
                    font=("Consolas", 8),
                    text_color="red",
                    fg_color="#ffffff"
                )
                pos_label.place(x=pos[0]+5, y=pos[1]+5)


def main():
    """Run the TaxAct Simulator."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )

    logger.info("Starting TaxAct Simulator")

    app = TaxActSimulator()
    app.mainloop()

    logger.info("TaxAct Simulator closed")


if __name__ == "__main__":
    main()
