"""Measure exact pixel displacement of a single scroll(-1) in TaxAct's client table.

Usage:
    1. Open TaxAct Client Manager, make sure client list is visible
    2. Run: python scripts/measure_scroll.py
    3. You have 3 seconds to hover your mouse over the client table
    4. Script takes screenshot, scrolls -1, takes another screenshot
    5. Uses template matching to calculate exact pixel shift
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
import pyautogui


def main():
    print("=== Scroll Pixel Measurement ===")
    print("Hover your mouse over the TaxAct client table.")
    print("Starting in 3 seconds...")
    time.sleep(3)

    # Define region to capture (left side of screen where client names are)
    # Capturing a vertical strip of the table
    region = (0, 150, 600, 650)  # x, y, w, h — covers the table area
    print(f"Capturing region: {region}")

    # Screenshot BEFORE scroll
    before = pyautogui.screenshot(region=region)
    before_np = cv2.cvtColor(np.array(before), cv2.COLOR_RGB2BGR)

    # Save before screenshot
    cv2.imwrite("scripts/scroll_before.png", before_np)
    print("Saved: scripts/scroll_before.png")

    # Perform scroll(-1) at current mouse position
    pos = pyautogui.position()
    print(f"Scrolling at mouse position: {pos}")
    pyautogui.scroll(-1, x=pos[0], y=pos[1])
    time.sleep(0.5)  # Wait for scroll to settle

    # Screenshot AFTER scroll
    after = pyautogui.screenshot(region=region)
    after_np = cv2.cvtColor(np.array(after), cv2.COLOR_RGB2BGR)

    # Save after screenshot
    cv2.imwrite("scripts/scroll_after.png", after_np)
    print("Saved: scripts/scroll_after.png")

    # Template matching: take a horizontal strip from the BEFORE image
    # (from the middle of the image to avoid header/edge effects)
    strip_y = 200  # Y offset within our captured region
    strip_h = 80   # Height of the strip
    template = before_np[strip_y:strip_y + strip_h, :, :]

    # Search for this strip in the AFTER image
    result = cv2.matchTemplate(after_np, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < 0.7:
        print(f"\nWARNING: Low confidence match ({max_val:.3f})")
        print("The scroll may have moved too much or too little.")
        print("Check the saved screenshots manually.")
        return

    matched_y = max_loc[1]
    pixel_shift = strip_y - matched_y

    print(f"\n=== RESULT ===")
    print(f"Match confidence: {max_val:.3f}")
    print(f"Template was at y={strip_y}, found at y={matched_y}")
    print(f"Pixel shift per scroll(-1): {pixel_shift} px")
    print(f"Row height (from settings): 32 px")

    if pixel_shift > 0:
        rows_per_scroll = pixel_shift / 32
        print(f"Rows per scroll: {rows_per_scroll:.2f}")

        # Find good scroll amounts (multiples of 32)
        print(f"\n=== RECOMMENDED SCROLL AMOUNTS ===")
        for n_rows in range(1, 20):
            target_px = n_rows * 32
            notches_needed = target_px / pixel_shift
            # Only show if close to integer
            if abs(notches_needed - round(notches_needed)) < 0.05:
                print(f"  scroll(-{round(notches_needed)}) = {n_rows} rows ({target_px}px)")
    else:
        print("No scroll detected! Make sure mouse is over the table.")


if __name__ == "__main__":
    main()
