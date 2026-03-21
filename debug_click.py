"""Debug script to calibrate the re-focus click position for preprocessing.

Shows a red splash at the configured click position so you can see
exactly where the bot would click to re-focus the TaxAct table.

Usage:
    1. Open TaxAct Client Manager on the primary monitor
    2. Run: python debug_click.py
    3. A red circle will flash at the current focus_click position
    4. Adjust focus_click_x / focus_click_y in config/settings.json
    5. Re-run to verify the new position

Controls:
    - Press SPACE to flash the red splash at the current position
    - Press Q to quit
    - Press C to click at the position (actually sends a click)
"""
import json
import threading
import time
import tkinter as tk
from pathlib import Path

import keyboard
import pyautogui

# Load settings
settings_path = Path(__file__).parent / "config" / "settings.json"
with open(settings_path) as f:
    settings = json.load(f)

preprocessing = settings.get("preprocessing", {})
focus_x = preprocessing.get("focus_click_x", 200)
focus_y = preprocessing.get("focus_click_y", 161)

print(f"=== Debug Click Position ===")
print(f"Current position: ({focus_x}, {focus_y})")
print(f"")
print(f"Controls:")
print(f"  SPACE  = Show red splash at position (no click)")
print(f"  C      = Show red splash AND click")
print(f"  Q      = Quit")
print(f"")
print(f"Edit config/settings.json -> preprocessing.focus_click_x / focus_click_y")


def show_splash(x: int, y: int, radius: int = 20, duration_ms: int = 600) -> None:
    """Show a red circle at (x, y) that fades after duration_ms."""
    def _run():
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", "white")
        root.geometry(f"{radius*4}x{radius*4}+{x - radius*2}+{y - radius*2}")

        canvas = tk.Canvas(root, width=radius*4, height=radius*4,
                           bg="white", highlightthickness=0)
        canvas.pack()

        # Outer ring
        canvas.create_oval(
            radius*2 - radius, radius*2 - radius,
            radius*2 + radius, radius*2 + radius,
            outline="red", width=3, fill=""
        )
        # Inner dot
        canvas.create_oval(
            radius*2 - 5, radius*2 - 5,
            radius*2 + 5, radius*2 + 5,
            fill="red", outline="red"
        )
        # Crosshair
        canvas.create_line(radius*2 - radius, radius*2,
                           radius*2 + radius, radius*2, fill="red", width=1)
        canvas.create_line(radius*2, radius*2 - radius,
                           radius*2, radius*2 + radius, fill="red", width=1)

        # Coordinates label
        canvas.create_text(radius*2, radius*2 + radius + 10,
                           text=f"({x}, {y})", fill="red", font=("Arial", 10, "bold"))

        root.after(duration_ms, root.destroy)
        root.mainloop()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def on_space():
    print(f"  Splash at ({focus_x}, {focus_y})")
    show_splash(focus_x, focus_y)


def on_click():
    print(f"  Splash + Click at ({focus_x}, {focus_y})")
    show_splash(focus_x, focus_y)
    time.sleep(0.1)
    pyautogui.click(focus_x, focus_y)


print("\nWaiting for input...")

keyboard.add_hotkey("space", on_space)
keyboard.add_hotkey("c", on_click)
keyboard.wait("q")
print("Done.")
