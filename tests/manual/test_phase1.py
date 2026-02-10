"""Manual integration test for Phase 1 components.

This script tests all Phase 1 modules interactively:
1. Imports all modules
2. Plays success sound
3. Prints screen resolution
4. Checks for TaxAct window
5. Optionally clicks at (100, 100)

Run with: python tests/manual/test_phase1.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def main():
    print("\n" + "=" * 50)
    print("Phase 1 Integration Test")
    print("=" * 50)

    # Test 1: Import all modules
    print("\n[1/5] Testing module imports...")
    try:
        from clickbot import sounds
        from clickbot import executor
        from clickbot import window_validator
        from clickbot.main import load_settings
        print("  OK: All modules imported successfully")
    except ImportError as e:
        print(f"  FAIL: Import error: {e}")
        return 1

    # Test 2: Play success sound
    print("\n[2/5] Testing sounds.play_success()...")
    try:
        sounds.play_success()
        print("  OK: Success sound played (did you hear it?)")
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 3: Get screen resolution
    print("\n[3/5] Testing window_validator.get_screen_resolution()...")
    try:
        width, height = window_validator.get_screen_resolution()
        print(f"  OK: Screen resolution is {width}x{height}")

        if width == 1920 and height == 1080:
            print("  OK: Resolution matches expected 1920x1080")
        else:
            print(f"  WARNING: Expected 1920x1080, got {width}x{height}")
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 4: Check for TaxAct window
    print("\n[4/5] Testing window_validator.find_taxact_window()...")
    try:
        window = window_validator.find_taxact_window()
        if window:
            print(f"  OK: TaxAct window found at ({window.left}, {window.top})")
            print(f"      Title: '{window.title}'")

            # Check if on primary monitor
            if window_validator.is_on_primary_monitor(window):
                print("  OK: TaxAct is on primary monitor")
            else:
                print("  WARNING: TaxAct is NOT on primary monitor!")
        else:
            print("  INFO: TaxAct window not found (open TaxAct to test)")
    except Exception as e:
        print(f"  FAIL: {e}")

    # Test 5: Optional click test
    print("\n[5/5] Click test (optional)...")
    response = input("  Do you want to test clicking at (100, 100)? [y/N]: ")

    if response.lower() == "y":
        try:
            print("  Moving mouse and clicking in 2 seconds...")
            executor.set_dev_mode(True)  # Slow mode for visibility
            executor.click(100, 100, wait=0.5)
            print("  OK: Click executed at (100, 100)")
        except Exception as e:
            print(f"  FAIL: {e}")
    else:
        print("  SKIPPED: Click test")

    # Summary
    print("\n" + "=" * 50)
    print("Phase 1 Integration Test Complete")
    print("=" * 50)

    # Play complete sound
    print("\nPlaying completion melody...")
    sounds.play_complete()

    print("\nNext step: Run 'python -m clickbot.main' to test hotkeys")
    return 0


if __name__ == "__main__":
    sys.exit(main())
