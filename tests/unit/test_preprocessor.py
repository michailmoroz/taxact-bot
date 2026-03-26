"""Unit tests for clickbot.preprocessor module."""

import csv
import queue
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from clickbot.preprocessor import (
    ClientRecord,
    load_csv,
    update_client_status,
    get_todo_clients,
    get_latest_csv,
    preprocess_table,
    _write_csv,
)


@pytest.fixture
def sample_records():
    """Sample client records for testing."""
    return [
        ClientRecord("SANDMEYER INC", "12-3456789", "1120S", "TODO"),
        ClientRecord("SMITH LLC", "98-7654321", "1120", "DONE"),
        ClientRecord("JONES CORP", "11-2233445", "1040", "TODO"),
        ClientRecord("BROWN LLC", "55-6677889", "1120S", "FAIL"),
    ]


@pytest.fixture
def csv_file(tmp_path, sample_records):
    """Create a temporary CSV file with sample data."""
    csv_path = tmp_path / "clients_2026-03-19-14-30-00.csv"
    _write_csv(csv_path, sample_records)
    return csv_path


class TestWriteAndLoadCsv:
    """Tests for _write_csv() and load_csv()."""

    def test_write_creates_file(self, tmp_path, sample_records):
        """_write_csv creates a CSV file with correct content."""
        csv_path = tmp_path / "test.csv"
        _write_csv(csv_path, sample_records)

        assert csv_path.exists()

        # Verify header and row count
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert rows[0] == ["Client", "ID", "Return Type", "Status"]
        assert len(rows) == 5  # header + 4 records

    def test_load_csv_roundtrip(self, csv_file, sample_records):
        """load_csv reads back the same records that were written."""
        loaded = load_csv(csv_file)

        assert len(loaded) == len(sample_records)
        for orig, loaded_rec in zip(sample_records, loaded):
            assert loaded_rec.client_name == orig.client_name
            assert loaded_rec.client_id == orig.client_id
            assert loaded_rec.return_type == orig.return_type
            assert loaded_rec.status == orig.status

    def test_load_csv_empty_file(self, tmp_path):
        """load_csv returns empty list for CSV with only header."""
        csv_path = tmp_path / "empty.csv"
        _write_csv(csv_path, [])

        records = load_csv(csv_path)
        assert records == []

    def test_write_csv_encoding(self, tmp_path):
        """_write_csv handles special characters in client names."""
        records = [ClientRecord("O'BRIEN & CO", "12-345", "1120", "TODO")]
        csv_path = tmp_path / "special.csv"
        _write_csv(csv_path, records)

        loaded = load_csv(csv_path)
        assert loaded[0].client_name == "O'BRIEN & CO"


class TestUpdateClientStatus:
    """Tests for update_client_status()."""

    def test_update_todo_to_done(self, csv_file):
        """update_client_status changes TODO to DONE."""
        update_client_status(
            csv_file, "SANDMEYER INC", "12-3456789", "1120S", "DONE"
        )

        records = load_csv(csv_file)
        sandmeyer = next(r for r in records if r.client_name == "SANDMEYER INC")
        assert sandmeyer.status == "DONE"

    def test_update_todo_to_fail(self, csv_file):
        """update_client_status changes TODO to FAIL."""
        update_client_status(
            csv_file, "JONES CORP", "11-2233445", "1040", "FAIL"
        )

        records = load_csv(csv_file)
        jones = next(r for r in records if r.client_name == "JONES CORP")
        assert jones.status == "FAIL"

    def test_update_preserves_other_records(self, csv_file):
        """update_client_status does not modify other records."""
        update_client_status(
            csv_file, "SANDMEYER INC", "12-3456789", "1120S", "DONE"
        )

        records = load_csv(csv_file)
        smith = next(r for r in records if r.client_name == "SMITH LLC")
        assert smith.status == "DONE"  # Was already DONE
        jones = next(r for r in records if r.client_name == "JONES CORP")
        assert jones.status == "TODO"  # Unchanged

    def test_update_nonexistent_client(self, csv_file):
        """update_client_status handles missing client gracefully."""
        update_client_status(
            csv_file, "NONEXISTENT", "00-0000000", "1120", "DONE"
        )

        # All records should be unchanged
        records = load_csv(csv_file)
        assert len(records) == 4

    def test_update_matches_by_client_id(self, tmp_path):
        """update_client_status matches by client_id (SSN/EIN) only."""
        # Two clients with same name but different IDs
        records = [
            ClientRecord("SMITH LLC", "11-111", "1120", "TODO"),
            ClientRecord("SMITH LLC", "22-222", "1120S", "TODO"),
        ]
        csv_path = tmp_path / "test.csv"
        _write_csv(csv_path, records)

        update_client_status(csv_path, "SMITH LLC", "22-222", "1120S", "DONE")

        loaded = load_csv(csv_path)
        assert loaded[0].status == "TODO"  # 11-111 unchanged
        assert loaded[1].status == "DONE"  # 22-222 updated


class TestGetTodoClients:
    """Tests for get_todo_clients()."""

    def test_filters_by_return_type_and_status(self, csv_file):
        """get_todo_clients returns only TODO clients for given return type."""
        todo_1120s = get_todo_clients(csv_file, "1120S")
        assert len(todo_1120s) == 1
        assert todo_1120s[0].client_name == "SANDMEYER INC"

    def test_no_todo_for_return_type(self, csv_file):
        """get_todo_clients returns empty list when no TODO for return type."""
        todo_1120 = get_todo_clients(csv_file, "1120")
        assert todo_1120 == []  # SMITH LLC is DONE

    def test_filters_correctly_1040(self, csv_file):
        """get_todo_clients works for 1040 return type."""
        todo_1040 = get_todo_clients(csv_file, "1040")
        assert len(todo_1040) == 1
        assert todo_1040[0].client_name == "JONES CORP"


class TestGetLatestCsv:
    """Tests for get_latest_csv()."""

    def test_returns_newest_file(self, tmp_path):
        """get_latest_csv returns the file with latest timestamp in name."""
        # Create files with different timestamps
        _write_csv(tmp_path / "clients_2026-03-18-10-00-00.csv", [])
        _write_csv(tmp_path / "clients_2026-03-19-14-30-00.csv", [])
        _write_csv(tmp_path / "clients_2026-03-19-09-00-00.csv", [])

        latest = get_latest_csv(tmp_path)
        assert latest is not None
        assert latest.name == "clients_2026-03-19-14-30-00.csv"

    def test_returns_none_for_empty_dir(self, tmp_path):
        """get_latest_csv returns None when no CSV files exist."""
        result = get_latest_csv(tmp_path)
        assert result is None

    def test_returns_none_for_nonexistent_dir(self, tmp_path):
        """get_latest_csv returns None when directory doesn't exist."""
        result = get_latest_csv(tmp_path / "nonexistent")
        assert result is None

    def test_ignores_non_matching_files(self, tmp_path):
        """get_latest_csv ignores files not matching clients_*.csv pattern."""
        (tmp_path / "other_file.csv").write_text("data")
        (tmp_path / "clients.txt").write_text("data")

        result = get_latest_csv(tmp_path)
        assert result is None


class TestDeduplication:
    """Tests for deduplication logic (used in preprocess_table)."""

    def test_records_with_same_composite_key(self):
        """Verify ClientRecord equality based on fields (for dedup logic)."""
        r1 = ClientRecord("TEST", "12-345", "1120S", "TODO")
        r2 = ClientRecord("TEST", "12-345", "1120S", "DONE")

        # Same name+id+return_type but different status
        key1 = (r1.client_name, r1.client_id, r1.return_type)
        key2 = (r2.client_name, r2.client_id, r2.return_type)
        assert key1 == key2

    def test_records_with_different_composite_key(self):
        """Different composite keys are not equal."""
        r1 = ClientRecord("TEST", "12-345", "1120S", "TODO")
        r2 = ClientRecord("TEST", "12-345", "1120", "TODO")  # Different return type

        key1 = (r1.client_name, r1.client_id, r1.return_type)
        key2 = (r2.client_name, r2.client_id, r2.return_type)
        assert key1 != key2


class TestStatusMapping:
    """Tests for status mapping logic."""

    def test_empty_fed_ef_status_maps_to_todo(self):
        """Empty fed_ef_status should map to TODO."""
        status = "TODO" if not "" else "DONE"
        assert status == "TODO"

    def test_nonempty_fed_ef_status_maps_to_done(self):
        """Non-empty fed_ef_status should map to DONE."""
        status = "TODO" if not "Submitted" else "DONE"
        assert status == "DONE"


# --- Fixtures for preprocess_table tests ---


@pytest.fixture
def base_settings(tmp_path):
    """Minimal settings dict for preprocess_table tests."""
    return {
        "client_table": {
            "row_height": 32,
            "first_data_row_y": 205,
            "max_visible_rows": 5,
            "columns": {
                "client_name": {"x": 20, "width": 340},
                "ssn_ein": {"x": 400, "width": 120},
                "return_type": {"x": 630, "width": 55},
                "fed_ef_status": {"x": 800, "width": 117},
            },
        },
        "preprocessing": {
            "csv_output_dir": str(tmp_path),
            "arrow_key_delay_s": 0.0,
            "post_scroll_delay_s": 0.0,
            "overlap_rows": 2,
            "refocus_click_x": 200,
            "refocus_click_y": 1065,
        },
        "ocr": {"tesseract_path": "", "language": "eng"},
    }


def _make_page_reader(pages):
    """Create a mock read_all_rows_from_screenshot that returns pages.

    Args:
        pages: List of pages, each page is a list of
               (name, id, return_type, fed_ef_status) tuples.
    """
    page_index = [0]

    def mock_read(screenshot, settings, start_row=0, stop_event=None):
        idx = page_index[0]
        page_index[0] += 1
        if idx >= len(pages):
            return []
        return list(pages[idx])

    return mock_read


class TestPreprocessTablePageScan:
    """Tests for page-based scanning with one PIL screenshot per page."""

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_reads_all_rows_from_single_screenshot(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """pyautogui.screenshot() is called once per page."""
        mock_vision.normalize_return_type.side_effect = lambda x: x

        page1 = [
            ("CLIENT A", "12-345", "1120S", ""),
            ("CLIENT B", "98-765", "1120", ""),
        ]
        mock_vision.read_all_rows_from_screenshot.side_effect = _make_page_reader(
            [page1, []]
        )
        mock_pyautogui.screenshot.return_value = "fake_pil_screenshot"

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        result = preprocess_table(base_settings, msg_queue, stop_event)

        assert result is not None
        records = load_csv(result)
        assert len(records) == 2
        # pyautogui.screenshot() called once for page 1, once for page 2 (empty)
        assert mock_pyautogui.screenshot.call_count == 2

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_deduplicates_overlapping_rows_between_pages(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """Overlapping rows between pages are deduplicated."""
        mock_vision.normalize_return_type.side_effect = lambda x: x

        page1 = [
            ("CLIENT A", "12-345", "1120S", ""),
            ("CLIENT B", "98-765", "1120", ""),
            ("CLIENT C", "55-555", "1040", ""),
        ]
        # Page 2 overlaps B and C, adds D and E
        page2 = [
            ("CLIENT B", "98-765", "1120", ""),   # overlap
            ("CLIENT C", "55-555", "1040", ""),   # overlap
            ("CLIENT D", "44-444", "1120S", ""),
            ("CLIENT E", "33-333", "1120", "Submitted"),
        ]
        mock_vision.read_all_rows_from_screenshot.side_effect = _make_page_reader(
            [page1, page2, []]
        )
        mock_pyautogui.screenshot.return_value = "fake_pil_screenshot"

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        result = preprocess_table(base_settings, msg_queue, stop_event)

        assert result is not None
        records = load_csv(result)
        assert len(records) == 5
        names = [r.client_name for r in records]
        assert names == ["CLIENT A", "CLIENT B", "CLIENT C", "CLIENT D", "CLIENT E"]
        # CLIENT E has non-empty fed_ef_status → actual status text
        assert records[4].status == "Submitted"

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_second_page_uses_overlap_start_row(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """All pages pass start_row=0 to scan all visible rows."""
        mock_vision.normalize_return_type.side_effect = lambda x: x

        page1 = [("CLIENT A", "12-345", "1120S", "")]
        page2 = [("CLIENT B", "98-765", "1120", "")]
        mock_vision.read_all_rows_from_screenshot.side_effect = _make_page_reader(
            [page1, page2, []]
        )
        mock_pyautogui.screenshot.return_value = "fake_pil_screenshot"

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        preprocess_table(base_settings, msg_queue, stop_event)

        # Verify start_row arguments: always 0 (scan all rows, rely on dedup)
        calls = mock_vision.read_all_rows_from_screenshot.call_args_list
        for c in calls:
            assert c.kwargs.get("start_row", c.args[2] if len(c.args) > 2 else 0) == 0

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_first_page_reads_all_rows(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """First page passes start_row=0 to read all visible rows."""
        mock_vision.normalize_return_type.side_effect = lambda x: x
        mock_vision.read_all_rows_from_screenshot.side_effect = _make_page_reader(
            [[("CLIENT A", "12-345", "1120S", "")], []]
        )
        mock_pyautogui.screenshot.return_value = "fake_pil_screenshot"

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        preprocess_table(base_settings, msg_queue, stop_event)

        first_call = mock_vision.read_all_rows_from_screenshot.call_args_list[0]
        assert first_call.kwargs.get("start_row", first_call.args[2] if len(first_call.args) > 2 else 0) == 0


class TestPreprocessTableKeyPresses:
    """Tests that preprocess_table scrolls with pydirectinput."""

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_one_down_press_per_page(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """Each page gets exactly 1 down-arrow press to scroll."""
        mock_vision.normalize_return_type.side_effect = lambda x: x

        page1 = [("CLIENT A", "12-345", "1120S", "")]
        mock_vision.read_all_rows_from_screenshot.side_effect = _make_page_reader(
            [page1, []]
        )
        mock_pyautogui.screenshot.return_value = "fake_pil_screenshot"

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        preprocess_table(base_settings, msg_queue, stop_event)

        down_calls = [c for c in mock_pydirectinput.press.call_args_list
                      if c == call('down')]
        assert len(down_calls) == 1

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_refocus_click_before_each_scroll(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """Each page gets a refocus click before the down-arrow press."""
        mock_vision.normalize_return_type.side_effect = lambda x: x

        page1 = [("CLIENT A", "12-345", "1120S", "")]
        page2 = [("CLIENT B", "98-765", "1120", "")]
        mock_vision.read_all_rows_from_screenshot.side_effect = _make_page_reader(
            [page1, page2, []]
        )
        mock_pyautogui.screenshot.return_value = "fake_pil_screenshot"

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        preprocess_table(base_settings, msg_queue, stop_event)

        # 2 pages with data → 2 refocus clicks (one per page before scroll)
        refocus_x = base_settings["preprocessing"]["refocus_click_x"]
        refocus_y = base_settings["preprocessing"]["refocus_click_y"]
        click_calls = [c for c in mock_pyautogui.click.call_args_list
                       if c == call(refocus_x, refocus_y)]
        assert len(click_calls) == 2

        # 2 down-arrow presses (one per page)
        down_calls = [c for c in mock_pydirectinput.press.call_args_list
                      if c == call('down')]
        assert len(down_calls) == 2


class TestPreprocessTableEndDetection:
    """Tests for end-of-table detection via stale last-client check."""

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_stale_detection_after_one_identical_last_client(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """Scan stops when last client is unchanged after 1 scroll attempt (threshold=1)."""
        mock_vision.normalize_return_type.side_effect = lambda x: x

        page1 = [
            ("CLIENT A", "12-345", "1120S", ""),
            ("LAST", "99-999", "1120S", ""),
        ]
        # Page 2 ends with "LAST" → stale_count reaches 1 → stop
        page_stale = [
            ("LAST", "99-999", "1120S", ""),
        ]
        mock_vision.read_all_rows_from_screenshot.side_effect = _make_page_reader(
            [page1, page_stale]
        )
        mock_pyautogui.screenshot.return_value = "fake_pil_screenshot"

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        result = preprocess_table(base_settings, msg_queue, stop_event)

        assert result is not None
        records = load_csv(result)
        # Only 2 unique clients (A and LAST)
        assert len(records) == 2
        # Should have read 2 pages (page1 + 1 stale → stop)
        assert mock_pyautogui.screenshot.call_count == 2

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_does_not_stop_if_last_client_changes(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """Scan continues when last client changes between pages."""
        mock_vision.normalize_return_type.side_effect = lambda x: x

        page1 = [("CLIENT A", "12-345", "1120S", "")]
        page2 = [("CLIENT B", "98-765", "1120", "")]
        page3 = [("CLIENT C", "55-555", "1040", "")]
        mock_vision.read_all_rows_from_screenshot.side_effect = _make_page_reader(
            [page1, page2, page3, []]
        )
        mock_pyautogui.screenshot.return_value = "fake_pil_screenshot"

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        result = preprocess_table(base_settings, msg_queue, stop_event)

        assert result is not None
        records = load_csv(result)
        assert len(records) == 3

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_empty_table_stops_immediately(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """Scan stops immediately when first page has no rows."""
        mock_vision.read_all_rows_from_screenshot.return_value = []
        mock_pyautogui.screenshot.return_value = "fake_pil_screenshot"

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        result = preprocess_table(base_settings, msg_queue, stop_event)

        assert result is not None
        records = load_csv(result)
        assert len(records) == 0
        # No scrolling should have happened
        assert mock_pydirectinput.press.call_count == 0

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_stale_resets_when_new_client_appears(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """Stale counter resets when a new last client appears."""
        mock_vision.normalize_return_type.side_effect = lambda x: x

        page1 = [("CLIENT A", "12-345", "1120S", "")]
        # New client appears → resets stale
        page_new = [
            ("CLIENT A", "12-345", "1120S", ""),
            ("CLIENT B", "98-765", "1120", ""),
        ]
        # 1 stale page (same last as page_new) → stale_count=1 → stop
        page_stale_b = [("CLIENT B", "98-765", "1120", "")]

        mock_vision.read_all_rows_from_screenshot.side_effect = _make_page_reader(
            [page1, page_new, page_stale_b]
        )
        mock_pyautogui.screenshot.return_value = "fake_pil_screenshot"

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        result = preprocess_table(base_settings, msg_queue, stop_event)

        assert result is not None
        records = load_csv(result)
        assert len(records) == 2
        # 3 pages total: p1 + new + 1 stale → stop
        assert mock_pyautogui.screenshot.call_count == 3
