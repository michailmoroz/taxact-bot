"""Preprocessing module for scanning TaxAct client table and exporting to CSV.

Scans the TaxAct Client Manager table page-by-page: takes one screenshot
per visible page, reads all rows via OCR, then scrolls down using arrow
keys and repeats. Deduplicates overlapping rows between pages.
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

    Takes one screenshot per visible page, reads all rows from it, then
    scrolls down by pressing the down arrow key max_visible_rows times.
    Repeats until end-of-table is detected (last client unchanged after
    3 consecutive scroll attempts). Deduplicates overlapping rows.

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

        # Read settings
        table_settings = settings.get("client_table", {})
        max_visible_rows = table_settings.get("max_visible_rows", 20)

        preprocessing_settings = settings.get("preprocessing", {})
        arrow_key_delay = preprocessing_settings.get("arrow_key_delay_s", 0.3)
        post_scroll_delay = preprocessing_settings.get("post_scroll_delay_s", 0.5)

        # Click on first row to give table keyboard focus
        focus_x = preprocessing_settings.get("focus_click_x", 200)
        focus_y = preprocessing_settings.get("focus_click_y", 161)
        pyautogui.click(focus_x, focus_y)
        time.sleep(0.3)

        # Page-by-page scan
        records: List[ClientRecord] = []
        seen_keys: set = set()
        prev_last_client = ""
        stale_count = 0
        max_pages = 500  # Safety limit
        total_rows_scanned = 0

        for page_num in range(max_pages):
            if stop_event.is_set():
                send_log("Preprocessing stopped by user")
                return None

            # Take one screenshot and read all visible rows from it
            screenshot = vision.take_screenshot()
            rows = vision.read_all_rows_from_screenshot(
                screenshot, column_positions, settings
            )

            if not rows:
                logger.debug(f"Page {page_num}: no rows found, end of table")
                break

            # Process each row from this page
            new_on_page = 0
            for client_name, client_id, raw_return_type, fed_ef_status in rows:
                return_type = vision.normalize_return_type(raw_return_type)
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
                    new_on_page += 1

            total_rows_scanned += len(rows)
            send_log(
                f"Page {page_num + 1}: {len(rows)} rows read, "
                f"{new_on_page} new ({len(records)} total)"
            )

            # End-of-table detection: compare last client on this page
            # with last client from the previous page
            last_client_on_page = rows[-1][0]  # client_name of last row

            if last_client_on_page == prev_last_client:
                stale_count += 1
                if stale_count >= 3:
                    logger.info(
                        f"End of table detected: last client '{last_client_on_page}' "
                        f"unchanged after {stale_count} scroll attempts"
                    )
                    send_log(f"End of table reached ({len(records)} clients)")
                    break
            else:
                stale_count = 0
            prev_last_client = last_client_on_page

            if stop_event.is_set():
                send_log("Preprocessing stopped by user")
                return None

            # Scroll down: press down arrow max_visible_rows times
            for _ in range(max_visible_rows):
                if stop_event.is_set():
                    send_log("Preprocessing stopped by user")
                    return None
                pydirectinput.press('down')
                time.sleep(arrow_key_delay)

            # Wait for TaxAct to finish rendering after scroll
            time.sleep(post_scroll_delay)

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
