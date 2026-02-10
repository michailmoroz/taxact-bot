"""Phase 3 Integration Test - Single Iteration (1120).

This test validates:
1. All new modules import correctly
2. Vision module can take screenshots
3. Process loader can load 1120.json
4. Process executor initializes

For FULL testing, TaxAct must be open with a 1120 client selected.
"""

import sys
from pathlib import Path


def main():
    print("\n" + "=" * 50)
    print("Phase 3 Integration Test")
    print("=" * 50)

    # Test 1: Import all new modules
    print("\n[1/6] Testing module imports...")
    try:
        from clickbot import vision
        from clickbot import process_loader
        from clickbot import process_executor
        print("  OK: All new modules imported successfully")
    except ImportError as e:
        print(f"  FAIL: Import error: {e}")
        return 1

    # Test 2: Load settings
    print("\n[2/6] Testing settings with vision config...")
    try:
        import json
        with open("config/settings.json", "r") as f:
            settings = json.load(f)

        assert "vision" in settings, "Missing 'vision' section"
        print(f"  OK: Vision config loaded (confidence={settings['vision']['confidence_threshold']})")
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Test 3: Vision module functions
    print("\n[3/6] Testing vision.take_screenshot()...")
    try:
        vision.configure(settings)
        screenshot = vision.take_screenshot()
        print(f"  OK: Screenshot captured ({screenshot.shape})")
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Test 4: Process loader
    print("\n[4/6] Testing process_loader.load_process('1120')...")
    try:
        process = process_loader.load_process("1120")
        print(f"  OK: Process loaded: {process['name']} ({len(process['steps'])} steps)")
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Test 5: Process executor initialization
    print("\n[5/6] Testing ProcessExecutor initialization...")
    try:
        import queue
        import threading

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        executor = process_executor.ProcessExecutor(settings, msg_queue, stop_event)
        print("  OK: ProcessExecutor initialized")
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Test 6: Check assets directory
    print("\n[6/6] Checking screenshot assets...")
    screenshot_base = Path(settings["vision"]["screenshot_base_path"])

    if screenshot_base.exists():
        common_files = list((screenshot_base / "common").glob("*.png")) if (screenshot_base / "common").exists() else []
        files_1120 = list((screenshot_base / "1120").glob("*.png")) if (screenshot_base / "1120").exists() else []
        print(f"  OK: Screenshot directory found")
        print(f"      common/: {len(common_files)} PNG files")
        print(f"      1120/: {len(files_1120)} PNG files")
        print(f"      Total: {len(common_files) + len(files_1120)} screenshots")

        if len(common_files) + len(files_1120) < 27:
            print("  WARNING: Expected 27 screenshots, some may be missing!")
    else:
        print(f"  WARNING: Screenshot directory not found: {screenshot_base}")

    # Summary
    print("\n" + "=" * 50)
    print("Phase 3 Basic Tests: PASSED")
    print("=" * 50)
    print("\nNEXT STEPS:")
    print("1. Ensure TaxAct 2025 is open with a 1120 client")
    print("2. Run 'python -m clickbot.gui' to start the bot")
    print("3. Press Start and monitor the automation")
    print("\nTo run full automation test:")
    print("  python -m clickbot.gui")

    return 0


if __name__ == "__main__":
    sys.exit(main())
