"""Debug script to visualize what OCR captures from the TaxAct client table.

Usage:
    1. Open TaxAct Client Manager on the primary monitor
    2. Run: python debug_ocr.py
    3. Check the generated debug_*.png files to verify regions are correct
    4. Adjust coordinates in config/settings.json if needed

Output files:
    debug_full_screenshot.png  - Full screen capture
    debug_row_N_COLUMN.png     - Cell crop for row N, column COLUMN
    debug_annotated.png - Full screenshot with colored rectangles showing all regions
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pyautogui
import pytesseract
from PIL import Image, ImageDraw, ImageFont

# Load settings
settings_path = Path(__file__).parent / "config" / "settings.json"
with open(settings_path) as f:
    settings = json.load(f)

# Configure Tesseract
tesseract_path = settings.get("ocr", {}).get("tesseract_path", "")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Read table config
table = settings["client_table"]
first_data_row_y = table["first_data_row_y"]
row_height = table["row_height"]
columns = table["columns"]

NUM_ROWS = 20  # How many rows to debug

print("=" * 60)
print("TaxAct Client Table OCR Debug")
print("=" * 60)
print(f"\nConfig from settings.json:")
print(f"  first_data_row_y = {first_data_row_y}")
print(f"  row_height       = {row_height}")
print(f"  columns:")
for col_name, col_cfg in columns.items():
    print(f"    {col_name:20s} x={col_cfg['x']:4d}  width={col_cfg['width']:4d}")

print(f"\nScanning {NUM_ROWS} rows...")
print(f"Taking screenshot...")

screenshot = pyautogui.screenshot()
screenshot.save("debug_full_screenshot.png")
print(f"  -> debug_full_screenshot.png ({screenshot.size[0]}x{screenshot.size[1]})")

# Create annotated copy
annotated = screenshot.copy()
draw = ImageDraw.Draw(annotated)

# Colors for each column
colors = {
    "client_name": (255, 0, 0),      # Red
    "ssn_ein": (255, 165, 0),        # Orange
    "return_type": (0, 255, 0),      # Green
    "fed_ef_status": (0, 100, 255),  # Blue
}

print(f"\n{'Row':<5} {'Column':<20} {'Region (x,y,w,h)':<25} {'OCR Result'}")
print("-" * 90)

for row_idx in range(NUM_ROWS):
    row_y = first_data_row_y + (row_idx * row_height)

    for col_name, col_cfg in columns.items():
        x = col_cfg["x"]
        w = col_cfg["width"]

        # Region coordinates
        x1, y1 = x, row_y
        x2, y2 = x + w, row_y + row_height

        # Crop and save
        region = screenshot.crop((x1, y1, x2, y2))
        filename = f"debug_row_{row_idx}_{col_name}.png"
        region.save(filename)

        # OCR with grayscale conversion (matches vision.py behavior)
        # Raw RGB can fail on colored text (e.g. blue status text)
        region_np = np.array(region)
        region_gray = cv2.cvtColor(region_np, cv2.COLOR_RGB2GRAY)
        region_pil = Image.fromarray(region_gray)
        text = pytesseract.image_to_string(region_pil, lang="eng").strip()

        # Take first non-empty line (like the bot does)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        result = lines[0] if lines else ""

        print(f"  {row_idx:<3} {col_name:<20} ({x1},{y1},{w},{row_height}){'':<5} '{result}'")

        # Draw rectangle on annotated image
        color = colors.get(col_name, (255, 255, 0))
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        # Label
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except Exception:
            font = ImageFont.load_default()
        label = f"{col_name} r{row_idx}"
        draw.text((x1 + 2, y1 - 14), label, fill=color, font=font)

    print()

# Save annotated screenshot
annotated.save("debug_annotated.png")
print(f"\n-> debug_annotated.png (full screenshot with colored region boxes)")
print(f"   Red = client_name, Orange = ssn_ein, Green = return_type, Blue = fed_ef_status")
print(f"\nDone! Check the debug_*.png files to verify regions are correct.")
