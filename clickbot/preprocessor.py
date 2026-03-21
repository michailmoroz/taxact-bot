"""Preprocessing module for scanning TaxAct client table and exporting to CSV.

Scans the complete TaxAct Client Manager table row-by-row using arrow key
navigation, extracts client data via OCR, deduplicates, and writes to CSV.
"""

import csv
import logging
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pydirectinput
import pyautogui

from clickbot import paths
from clickbot import sounds
from clickbot import vision
from clickbot import winkeys
from clickbot.bot_controller import StatusMessage

logger = logging.getLogger(__name__)


@dataclass
class ClientRecord:
    """A single client record from the preprocessing scan."""
    client_name: str
    client_id: str       # SSN/EIN
    return_type: str
    status: str          # TODO, DONE, FAIL


CSV_COLUMNS = ["Client", "ID", "Return Type", "Status"]


def preprocess_table(
    settings: dict,
    message_queue: queue.Queue,
    stop_event: threading.Event,
) -> Optional[Path]:
    """Scan the complete TaxAct client table and export to CSV.

    Navigates row-by-row using the down arrow key, reads all 4 columns
    via OCR, deduplicates, and writes the result to a timestamped CSV file.

    Args:
        settings: Settings dict from config/settings.json
        message_queue: Queue for sending status updates to GUI
        stop_event: Event to signal stop

    Returns:
        Path to the created CSV file, or None on error/stop
    """
    def send_log(msg: str) -> None:
        message_queue.put(StatusMessage("log", msg))

    def send_status(msg: str) -> None:
        message_queue.put(StatusMessage("status", msg))

    def send_error(msg: str) -> None:
        message_queue.put(StatusMessage("error", msg))

    try:
        # Configure vision module
        vision.configure(settings)
        vision.configure_tesseract(settings)

        send_status("Preprocessing: scanning table...")
        send_log("Starting preprocessing...")

        if stop_event.is_set():
            return None

        # Find column headers (including SSN/EIN)
        send_log("Finding column headers...")
        column_positions = vision.get_column_positions(extra_columns=["ssn_ein"])
        if column_positions is None:
            send_error("Column headers not found (including SSN/EIN). "
                       "Make sure TaxAct Client Manager is visible.")
            return None

        send_log(f"Found columns: {list(column_positions.keys())}")

        # Read table settings
        table_settings = settings.get("client_table", {})
        first_data_row_y = table_settings.get("first_data_row_y", 205)
        row_height = table_settings.get("row_height", 32)
        max_visible_rows = table_settings.get("max_visible_rows", 27)

        preprocessing_settings = settings.get("preprocessing", {})
        arrow_key_delay = preprocessing_settings.get("arrow_key_delay_s", 0.3)
        scroll_reset_row = preprocessing_settings.get("scroll_reset_row", 8)
        end_repeat_threshold = preprocessing_settings.get("end_repeat_threshold", 4)

        # Click on table to give it keyboard focus
        focus_x = preprocessing_settings.get("focus_click_x", 200)
        focus_y = preprocessing_settings.get("focus_click_y", 161)
        pyautogui.click(focus_x, focus_y)
        time.sleep(0.3)

        # Scroll to top of table (atomic SendInput with proper scan codes
        # and KEYEVENTF_EXTENDEDKEY — pyautogui/pydirectinput both fail here)
        winkeys.send_ctrl_home()
        time.sleep(0.5)

        # Re-click to ensure table has keyboard focus after scroll
        pyautogui.click(focus_x, focus_y)
        time.sleep(0.3)

        # Scan rows one by one using arrow key navigation
        records: List[ClientRecord] = []
        seen_keys: set = set()
        current_visual_row = 0
        prev_client_name = ""
        repeat_count = 0
        max_rows = 5000  # Safety limit

        for row_num in range(max_rows):
            if stop_event.is_set():
                send_log("Preprocessing stopped by user")
                return None

            # Calculate Y position for reading
            row_y = first_data_row_y + (current_visual_row * row_height)

            # Read all 4 columns
            client_name = vision._read_single_cell(
                "client_name", row_y, column_positions, settings
            )

            # Empty client_name = end of table
            if not client_name:
                logger.debug(f"Row {row_num}: empty client_name, end of table")
                break

            # End-of-table detection: N identical reads in a row = table end
            if client_name == prev_client_name:
                repeat_count += 1
                if repeat_count >= end_repeat_threshold:
                    logger.info(
                        f"End of table detected: '{client_name}' "
                        f"read {repeat_count + 1} times"
                    )
                    send_log(f"End of table reached (after {row_num + 1} rows)")
                    break
            else:
                repeat_count = 0
            prev_client_name = client_name

            client_id = vision._read_single_cell(
                "ssn_ein", row_y, column_positions, settings
            )
            raw_return_type = vision._read_single_cell(
                "return_type", row_y, column_positions, settings
            )
            fed_ef_status = vision._read_single_cell(
                "fed_ef_status", row_y, column_positions, settings
            )

            return_type = vision.normalize_return_type(raw_return_type)

            # Deduplicate
            current_key = (client_name, client_id, return_type)
            if current_key not in seen_keys:
                seen_keys.add(current_key)
                status = "TODO" if not fed_ef_status else "DONE"
                records.append(ClientRecord(
                    client_name=client_name,
                    client_id=client_id,
                    return_type=return_type,
                    status=status,
                ))
                sounds.play_iteration()

            # Log progress every 10 clients
            if (row_num + 1) % 10 == 0:
                send_log(f"Scanned {row_num + 1} rows...")

            # Press down arrow to move to next row (pydirectinput sends
            # proper scan codes + extended key flag via SendInput)
            pydirectinput.press('down')
            time.sleep(arrow_key_delay)

            # Track visual row position
            if current_visual_row < max_visible_rows - 1:
                current_visual_row += 1
            else:
                # TaxAct chunk-scrolls: the focused row jumps from the bottom
                # to a middle position (e.g., row 20 becomes row 9).
                current_visual_row = scroll_reset_row

        if stop_event.is_set():
            return None

        # Write CSV
        csv_dir = Path(preprocessing_settings.get(
            "csv_output_dir", "C:/TaxActBot/logs"
        ))
        csv_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        csv_path = csv_dir / f"clients_{timestamp}.csv"

        _write_csv(csv_path, records)

        todo_count = sum(1 for r in records if r.status == "TODO")
        done_count = sum(1 for r in records if r.status == "DONE")

        send_log(
            f"Preprocessing complete! Found {len(records)} clients "
            f"({todo_count} TODO, {done_count} DONE)"
        )
        message_queue.put(StatusMessage("complete", str(csv_path)))

        logger.info(f"Preprocessing finished: {len(records)} clients -> {csv_path}")
        return csv_path

    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        send_error(f"Preprocessing failed: {e}")
        return None


def _write_csv(csv_path: Path, records: List[ClientRecord]) -> None:
    """Write client records to a CSV file.

    Args:
        csv_path: Path to write the CSV file
        records: List of ClientRecord to write
    """
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow({
                "Client": record.client_name,
                "ID": record.client_id,
                "Return Type": record.return_type,
                "Status": record.status,
            })
    logger.debug(f"Wrote {len(records)} records to {csv_path}")


def load_csv(csv_path: Path) -> List[ClientRecord]:
    """Load client records from a CSV file.

    Args:
        csv_path: Path to the CSV file

    Returns:
        List of ClientRecord
    """
    records = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(ClientRecord(
                client_name=row.get("Client", ""),
                client_id=row.get("ID", ""),
                return_type=row.get("Return Type", ""),
                status=row.get("Status", "TODO"),
            ))
    logger.debug(f"Loaded {len(records)} records from {csv_path}")
    return records


def update_client_status(
    csv_path: Path,
    client_name: str,
    client_id: str,
    return_type: str,
    new_status: str,
) -> None:
    """Update the status of a client in the CSV file.

    Finds the client by composite key (name, id, return_type) and updates
    the status. Writes the entire CSV back to disk.

    Args:
        csv_path: Path to the CSV file
        client_name: Client name to match
        client_id: SSN/EIN to match
        return_type: Return type to match
        new_status: New status value (TODO, DONE, FAIL)
    """
    records = load_csv(csv_path)
    updated = False

    for record in records:
        if (record.client_name == client_name
                and record.client_id == client_id
                and record.return_type == return_type):
            record.status = new_status
            updated = True
            logger.debug(
                f"Updated status: {client_name} ({client_id}, {return_type}) -> {new_status}"
            )
            break

    if not updated:
        logger.warning(
            f"Client not found in CSV: {client_name} ({client_id}, {return_type})"
        )
        return

    _write_csv(csv_path, records)


def get_todo_clients(csv_path: Path, return_type: str) -> List[ClientRecord]:
    """Get all TODO clients for a specific return type.

    Args:
        csv_path: Path to the CSV file
        return_type: Return type to filter by (e.g. "1120S")

    Returns:
        List of ClientRecord with status == "TODO" and matching return type
    """
    records = load_csv(csv_path)
    todo = [
        r for r in records
        if r.return_type == return_type and r.status == "TODO"
    ]
    logger.debug(f"Found {len(todo)} TODO clients for return type {return_type}")
    return todo


def get_latest_csv(csv_dir: Optional[Path] = None) -> Optional[Path]:
    """Find the most recent preprocessing CSV file.

    Args:
        csv_dir: Directory to search in. Defaults to C:/TaxActBot/logs

    Returns:
        Path to the newest clients_*.csv file, or None if none found
    """
    if csv_dir is None:
        csv_dir = paths.get_csv_dir()

    if not csv_dir.exists():
        return None

    csv_files = sorted(csv_dir.glob("clients_*.csv"))
    if not csv_files:
        return None

    return csv_files[-1]
