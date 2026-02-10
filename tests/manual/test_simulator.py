"""Test script for TaxAct Simulator.

Usage:
    1. Run this script to start the simulator
    2. In another terminal, run: python -m clickbot.gui
    3. The bot should interact with the simulator
"""

import subprocess
import sys
import time


def main():
    print("=" * 60)
    print("TaxAct Simulator Test")
    print("=" * 60)

    print("\n[1/2] Starting TaxAct Simulator...")
    print("      The simulator window will open at 1920x1080")
    print()
    print("INSTRUCTIONS:")
    print("  1. Position the simulator window at (0,0) - top-left of primary monitor")
    print("  2. In a NEW terminal, run: python -m clickbot.gui")
    print("  3. Click 'Start Bot' and watch it interact with the simulator")
    print()
    print("Press Ctrl+C to stop the simulator.")
    print()

    # Start simulator
    try:
        subprocess.run([sys.executable, "-m", "simulator.taxact_simulator"])
    except KeyboardInterrupt:
        print("\nSimulator stopped.")


if __name__ == "__main__":
    main()
