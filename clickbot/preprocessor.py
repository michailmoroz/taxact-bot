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
        # Configure tesseract for OCR
        vision.configure_tesseract(settings)

        send_status("Preprocessing: scanning table...")
        send_log("Starting preprocessing...")

        if stop_event.is_set():
            return None

        # Read settings
        table_settings = settings.get("client_table", {})
        max_visible_rows = table_settings.get("max_visible_rows", 20)

        preprocessing_settings = settings.get("preprocessing", {})
        arrow_key_delay = preprocessing_settings.get("arrow_key_delay_s", 0.3)
        post_scroll_delay = preprocessing_settings.get("post_scroll_delay_s", 0.5)
        overlap_rows = preprocessing_settings.get("overlap_rows", 9)
        refocus_x = preprocessing_settings.get("refocus_click_x", 200)
        refocus_y = preprocessing_settings.get("refocus_click_y", 1065)

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

            # Take PIL screenshot and read rows (debug_ocr.py approach)
            screenshot = pyautogui.screenshot()
            start_row = 0
            rows = vision.read_all_rows_from_screenshot(
                screenshot, settings, start_row=start_row,
                stop_event=stop_event,
            )

            if stop_event.is_set():
                send_log("Preprocessing stopped by user")
                return None

            if not rows:
                # Save debug screenshot for diagnosis
                debug_path = Path(preprocessing_settings.get(
                    "csv_output_dir", "C:/TaxActBot/logs"
                )) / f"debug_page_{page_num + 1}.png"
                try:
                    screenshot.save(str(debug_path))
                    send_log(
                        f"Page {page_num + 1}: 0 rows found — stopped. "
                        f"Screenshot saved: {debug_path.name}"
                    )
                    logger.info(f"Debug screenshot saved: {debug_path}")
                except Exception as e:
                    send_log(f"Page {page_num + 1}: 0 rows found — stopped.")
                    logger.warning(f"Could not save debug screenshot: {e}")
                break

            # Process each row from this page
            new_on_page = 0
            for client_name, client_id, raw_return_type, fed_ef_status in rows:
                return_type = vision.normalize_return_type(raw_return_type)
                current_key = (client_name, client_id, return_type)

                if current_key not in seen_keys:
                    seen_keys.add(current_key)
                    status = "TODO" if not fed_ef_status else fed_ef_status
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

            # Re-focus table (click last visible row) then scroll down
            pyautogui.click(refocus_x, refocus_y)
            if stop_event.wait(0.2):
                send_log("Preprocessing stopped by user")
                return None

            pydirectinput.press('down')
            if stop_event.wait(post_scroll_delay):
                send_log("Preprocessing stopped by user")
                return None

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
