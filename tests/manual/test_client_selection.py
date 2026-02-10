"""Client Selection Test - Scan Client Manager Table.

This test validates:
1. Column headers can be found via template matching
2. Table rows can be scanned via OCR
3. find_next_client() returns correct data

For FULL testing, TaxAct must be open with Client Manager visible.
"""

import sys
import json
from pathlib import Path


def main():
    print("\n" + "=" * 50)
    print("Client Selection Integration Test")
    print("=" * 50)

    # Test 1: Import modules
    print("\n[1/6] Testing module imports...")
    try:
        from clickbot import vision
        from clickbot.vision import (
            get_column_positions,
            scan_table_row,
            find_next_client,
            ClientRow
        )
        print("  OK: All client selection functions imported")
    except ImportError as e:
        print(f"  FAIL: Import error: {e}")
        return 1

    # Test 2: Load settings
    print("\n[2/6] Testing settings with client_table config...")
    try:
        with open("config/settings.json", "r") as f:
            settings = json.load(f)

        assert "client_table" in settings, "Missing 'client_table' section"
        table_config = settings["client_table"]
        print(f"  OK: client_table config found")
        print(f"      row_height: {table_config.get('row_height')}px")
        print(f"      first_data_row_y: {table_config.get('first_data_row_y')}px")
        print(f"      max_visible_rows: {table_config.get('max_visible_rows')}")
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Test 3: Check column header templates exist
    print("\n[3/6] Checking column header templates...")
    screenshot_base = Path(settings["vision"]["screenshot_base_path"])
    required_templates = [
        "common/column_header_client_name.png",
        "common/column_header_return_type.png",
        "common/column_header_fed_ef_status.png",
    ]
    all_found = True
    for template in required_templates:
        template_path = screenshot_base / template
        if template_path.exists():
            print(f"  OK: {template}")
        else:
            print(f"  MISSING: {template}")
            all_found = False

    if not all_found:
        print("\n  WARNING: Some templates missing - OCR fallback will be used")

    # Test 4: Configure vision module
    print("\n[4/6] Configuring vision module...")
    try:
        vision.configure(settings)
        vision.configure_tesseract(settings)
        print("  OK: Vision module configured")
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Test 5: Take screenshot (ensure screen is visible)
    print("\n[5/6] Taking test screenshot...")
    try:
        screenshot = vision.take_screenshot()
        print(f"  OK: Screenshot captured ({screenshot.shape})")
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Test 6: Find column positions (requires TaxAct Client Manager visible)
    print("\n[6/6] Finding column positions (requires Client Manager visible)...")
    try:
        column_positions = get_column_positions()
        if column_positions is None:
            print("  SKIP: Column headers not found - is Client Manager visible?")
            print("        This is expected if TaxAct is not open.")
        else:
            print("  OK: Column positions found:")
            for col_name, (x_pos, width) in column_positions.items():
                print(f"      {col_name}: x={x_pos}, width={width}")
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Summary
    print("\n" + "=" * 50)
    print("Client Selection Basic Tests: PASSED")
    print("=" * 50)

    print("\n" + "-" * 50)
    print("LIVE TEST (requires TaxAct with Client Manager visible)")
    print("-" * 50)
    response = input("\nRun live client scan? (y/N): ").strip().lower()

    if response == "y":
        print("\nRunning find_next_client()...")
        try:
            result = find_next_client(settings, "1120")
            if result is None:
                print("  Result: No unprocessed 1120 clients found")
                print("  (All clients may have Fed EF Status filled, or no 1120 clients exist)")
            else:
                client_row, click_pos = result
                print(f"  Result: Found client!")
                print(f"    Name: {client_row.client_name}")
                print(f"    Return Type: {client_row.return_type}")
                print(f"    Fed EF Status: '{client_row.fed_ef_status}' (empty = good)")
                print(f"    Row Index: {client_row.row_index}")
                print(f"    Click Position: ({click_pos[0]}, {click_pos[1]})")
        except Exception as e:
            print(f"  FAIL: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        print("\nSkipped live test.")

    print("\n" + "=" * 50)
    print("Test Complete")
    print("=" * 50)
    print("\nTo run full automation:")
    print("  python -m clickbot.gui")

    return 0


if __name__ == "__main__":
    sys.exit(main())
