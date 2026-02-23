"""Main entry point for TaxAct Form 7004 Automation Bot.

Handles:
- Loading configuration
- Setting up logging
- Registering hotkeys (F6 start, F7 stop, F8 pause)
- Bot state management
- Orchestrating the automation flow
"""

import json
import logging
import logging.handlers
import sys
from pathlib import Path

import keyboard

from clickbot import paths
from clickbot import sounds
from clickbot import executor
from clickbot import window_validator

logger = logging.getLogger(__name__)


class BotState:
    """Enumeration of bot states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"


# Module-level state
_current_state = BotState.IDLE
_settings = None
_should_stop = False


def load_settings(path: Path) -> dict:
    """Load settings from JSON file.

    Args:
        path: Path to settings.json file

    Returns:
        Settings dict

    Raises:
        FileNotFoundError: If settings file doesn't exist
        json.JSONDecodeError: If settings file is invalid JSON
    """
    logger.info(f"Loading settings from {path}")

    with open(path, "r", encoding="utf-8") as f:
        settings = json.load(f)

    logger.debug(f"Settings loaded: dev_mode={settings.get('dev_mode')}")
    return settings


def setup_logging(dev_mode: bool = False) -> None:
    """Configure logging for the bot.

    Args:
        dev_mode: If True, use DEBUG level; otherwise INFO
    """
    # Create logs directory if needed
    log_dir = paths.get_log_dir()

    # Set log level based on dev_mode
    log_level = logging.DEBUG if dev_mode else logging.INFO

    # Console formatter (simple)
    console_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )

    # File formatter (detailed)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "bot.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logger.info(f"Logging configured: level={logging.getLevelName(log_level)}")


def on_start() -> None:
    """Handle F6 (start) hotkey press."""
    global _current_state, _should_stop

    if _current_state == BotState.RUNNING:
        logger.info("Bot is already running")
        return

    if _current_state == BotState.PAUSED:
        logger.info("Resuming bot from paused state")
        _current_state = BotState.RUNNING
        return

    logger.info("Starting bot...")
    _should_stop = False

    # Validate startup
    success, message = window_validator.validate_startup(_settings)

    if not success:
        logger.error(f"Startup validation failed: {message}")
        sounds.play_error()
        print(f"\nERROR: {message}")
        return

    _current_state = BotState.RUNNING
    sounds.play_success()
    print(f"\nBot started. {message}")
    logger.info("Bot is now running")

    # TODO: In Phase 2, this will trigger the actual automation loop


def on_stop() -> None:
    """Handle F7 (stop) hotkey press."""
    global _current_state, _should_stop

    if _current_state == BotState.IDLE:
        logger.info("Bot is already stopped")
        return

    logger.info("Stopping bot...")
    _should_stop = True
    _current_state = BotState.IDLE
    print("\nBot stopped.")


def on_pause() -> None:
    """Handle F8 (pause) hotkey press."""
    global _current_state

    if _current_state == BotState.IDLE:
        logger.info("Cannot pause: bot is not running")
        return

    if _current_state == BotState.RUNNING:
        _current_state = BotState.PAUSED
        logger.info("Bot paused")
        print("\nBot paused. Press F6 to resume or F7 to stop.")
    elif _current_state == BotState.PAUSED:
        _current_state = BotState.RUNNING
        logger.info("Bot resumed")
        print("\nBot resumed.")


def get_state() -> str:
    """Get the current bot state.

    Returns:
        Current state string (idle, running, paused)
    """
    return _current_state


def main() -> None:
    """Main entry point."""
    global _settings

    # Load settings (copies default to %APPDATA% on first run when frozen)
    settings_path = paths.ensure_user_config()

    try:
        _settings = load_settings(settings_path)
    except FileNotFoundError:
        print(f"ERROR: Settings file not found: {settings_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in settings file: {e}")
        sys.exit(1)

    # Setup logging
    setup_logging(_settings.get("dev_mode", False))

    # Configure modules based on settings
    sounds.set_enabled(_settings.get("sounds", {}).get("enabled", True))
    executor.set_dev_mode(_settings.get("dev_mode", False))

    # Register hotkeys
    hotkeys = _settings.get("hotkeys", {})
    start_key = hotkeys.get("start", "F6")
    stop_key = hotkeys.get("stop", "F7")
    pause_key = hotkeys.get("pause", "F8")

    keyboard.add_hotkey(start_key, on_start)
    keyboard.add_hotkey(stop_key, on_stop)
    keyboard.add_hotkey(pause_key, on_pause)

    logger.info(f"Hotkeys registered: {start_key}=start, {stop_key}=stop, {pause_key}=pause")

    # Print startup message
    print("\n" + "=" * 50)
    print("TaxAct Form 7004 Automation Bot v0.1.0")
    print("=" * 50)
    print(f"\nHotkeys:")
    print(f"  {start_key} - Start bot")
    print(f"  {stop_key} - Stop bot")
    print(f"  {pause_key} - Pause/Resume bot")
    print(f"\nDev mode: {'ON' if _settings.get('dev_mode') else 'OFF'}")
    print(f"Sounds: {'ON' if _settings.get('sounds', {}).get('enabled') else 'OFF'}")
    print("\nBot ready. Press F6 to start.")
    print("Press Ctrl+C to exit.\n")

    # Keep script running
    try:
        keyboard.wait()  # Wait forever until interrupted
    except KeyboardInterrupt:
        logger.info("Bot terminated by user (Ctrl+C)")
        print("\nExiting...")


if __name__ == "__main__":
    main()
