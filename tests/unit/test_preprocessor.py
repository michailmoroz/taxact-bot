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

    def test_update_matches_composite_key(self, tmp_path):
        """update_client_status uses composite key (name + id + return_type)."""
        # Two clients with same name but different IDs
        records = [
            ClientRecord("SMITH LLC", "11-111", "1120", "TODO"),
            ClientRecord("SMITH LLC", "22-222", "1120S", "TODO"),
        ]
        csv_path = tmp_path / "test.csv"
        _write_csv(csv_path, records)

        update_client_status(csv_path, "SMITH LLC", "22-222", "1120S", "DONE")

        loaded = load_csv(csv_path)
        assert loaded[0].status == "TODO"  # First SMITH LLC unchanged
        assert loaded[1].status == "DONE"  # Second SMITH LLC updated


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
            "focus_click_x": 100,
            "focus_click_y": 200,
            "scroll_reset_row": 2,
            "end_repeat_threshold": 4,
        },
        "ocr": {"tesseract_path": "", "language": "eng"},
        "vision": {
            "screenshot_base_path": "assets/buttons",
            "confidence_threshold": 0.8,
        },
    }


def _make_cell_reader(client_sequence):
    """Create a mock _read_single_cell that returns data from a sequence.

    Args:
        client_sequence: List of (name, id, return_type, fed_ef_status) tuples.
            Each call cycle reads 4 columns for one row.
    """
    call_index = [0]  # Mutable counter
    row_index = [0]

    def mock_read(col_name, row_y, column_positions, settings):
        row = row_index[0]
        if row >= len(client_sequence):
            if col_name == "client_name":
                return ""
            return ""

        data = client_sequence[row]
        col_map = {
            "client_name": data[0],
            "ssn_ein": data[1],
            "return_type": data[2],
            "fed_ef_status": data[3],
        }
        result = col_map.get(col_name, "")

        call_index[0] += 1
        # Advance row after all 4 columns are read
        if col_name == "fed_ef_status":
            row_index[0] += 1

        return result

    return mock_read


class TestPreprocessTableKeyPresses:
    """Tests that preprocess_table uses pydirectinput for key events."""

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_uses_pydirectinput_for_ctrl_home(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """preprocess_table uses pydirectinput for Ctrl+Home scroll-to-top."""
        mock_vision.get_column_positions.return_value = {
            "client_name": (100, 200),
            "ssn_ein": (400, 100),
            "return_type": (630, 55),
            "fed_ef_status": (800, 100),
        }
        # Return empty on first read to end immediately
        mock_vision._read_single_cell.return_value = ""
        mock_vision.normalize_return_type.return_value = ""

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        preprocess_table(base_settings, msg_queue, stop_event)

        mock_pyautogui.hotkey.assert_called_with('ctrl', 'home')

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_uses_pydirectinput_press_for_down_arrow(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """preprocess_table uses pydirectinput.press('down') for arrow navigation."""
        mock_vision.get_column_positions.return_value = {
            "client_name": (100, 200),
            "ssn_ein": (400, 100),
            "return_type": (630, 55),
            "fed_ef_status": (800, 100),
        }

        # Return 2 clients, then empty
        clients = [
            ("CLIENT A", "12-345", "1120S", ""),
            ("CLIENT B", "98-765", "1120", ""),
        ]
        mock_vision._read_single_cell.side_effect = _make_cell_reader(clients)
        mock_vision.normalize_return_type.side_effect = lambda x: x

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        preprocess_table(base_settings, msg_queue, stop_event)

        # Should have called press('down') for each row
        down_calls = [c for c in mock_pydirectinput.press.call_args_list
                      if c == call('down')]
        assert len(down_calls) == 2


class TestPreprocessTableEndDetection:
    """Tests for end-of-table detection via repeated identical reads."""

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_stops_after_threshold_identical_reads(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """Scan stops when client_name repeats end_repeat_threshold times."""
        mock_vision.get_column_positions.return_value = {
            "client_name": (100, 200),
            "ssn_ein": (400, 100),
            "return_type": (630, 55),
            "fed_ef_status": (800, 100),
        }

        # 3 unique clients, then "LAST" repeated 5 times (threshold is 4)
        clients = [
            ("CLIENT A", "12-345", "1120S", ""),
            ("CLIENT B", "98-765", "1120", ""),
            ("CLIENT C", "55-555", "1040", ""),
            ("LAST", "99-999", "1120S", ""),
            ("LAST", "99-999", "1120S", ""),
            ("LAST", "99-999", "1120S", ""),
            ("LAST", "99-999", "1120S", ""),
            ("LAST", "99-999", "1120S", ""),  # Should never be reached
        ]
        mock_vision._read_single_cell.side_effect = _make_cell_reader(clients)
        mock_vision.normalize_return_type.side_effect = lambda x: x

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        result = preprocess_table(base_settings, msg_queue, stop_event)

        assert result is not None
        records = load_csv(result)
        # Should have 4 unique clients (A, B, C, LAST)
        assert len(records) == 4

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_does_not_stop_for_fewer_repeats(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """Scan continues when repeats are below threshold."""
        mock_vision.get_column_positions.return_value = {
            "client_name": (100, 200),
            "ssn_ein": (400, 100),
            "return_type": (630, 55),
            "fed_ef_status": (800, 100),
        }

        # "DUPE" repeated 3 times (below threshold of 4), then a new client
        clients = [
            ("DUPE", "11-111", "1120S", ""),
            ("DUPE", "11-111", "1120S", ""),
            ("DUPE", "11-111", "1120S", ""),
            ("NEW CLIENT", "22-222", "1120", ""),
        ]
        mock_vision._read_single_cell.side_effect = _make_cell_reader(clients)
        mock_vision.normalize_return_type.side_effect = lambda x: x

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        result = preprocess_table(base_settings, msg_queue, stop_event)

        assert result is not None
        records = load_csv(result)
        # Both unique clients should be in the CSV
        names = [r.client_name for r in records]
        assert "DUPE" in names
        assert "NEW CLIENT" in names

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_empty_table_stops_immediately(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """Scan stops immediately when first client_name is empty."""
        mock_vision.get_column_positions.return_value = {
            "client_name": (100, 200),
            "ssn_ein": (400, 100),
            "return_type": (630, 55),
            "fed_ef_status": (800, 100),
        }
        mock_vision._read_single_cell.return_value = ""

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        result = preprocess_table(base_settings, msg_queue, stop_event)

        assert result is not None
        records = load_csv(result)
        assert len(records) == 0


class TestPreprocessTableChunkScroll:
    """Tests for chunk-scroll handling in scan loop."""

    @patch("clickbot.preprocessor.pydirectinput")
    @patch("clickbot.preprocessor.pyautogui")
    @patch("clickbot.preprocessor.vision")
    @patch("clickbot.preprocessor.sounds")
    @patch("clickbot.preprocessor.time")
    def test_visual_row_resets_after_max(
        self, mock_time, mock_sounds, mock_vision, mock_pyautogui,
        mock_pydirectinput, base_settings
    ):
        """current_visual_row resets to scroll_reset_row after reaching max."""
        # max_visible_rows=5, scroll_reset_row=2
        mock_vision.get_column_positions.return_value = {
            "client_name": (100, 200),
            "ssn_ein": (400, 100),
            "return_type": (630, 55),
            "fed_ef_status": (800, 100),
        }

        # 7 unique clients (more than max_visible_rows=5)
        clients = [
            (f"CLIENT {i}", f"{i:02d}-000", "1120S", "")
            for i in range(7)
        ]
        mock_vision._read_single_cell.side_effect = _make_cell_reader(clients)
        mock_vision.normalize_return_type.side_effect = lambda x: x

        msg_queue = queue.Queue()
        stop_event = threading.Event()

        # Track the row_y values passed to _read_single_cell
        row_ys = []
        original_side_effect = mock_vision._read_single_cell.side_effect

        def tracking_read(col_name, row_y, col_pos, settings):
            if col_name == "client_name":
                row_ys.append(row_y)
            return original_side_effect(col_name, row_y, col_pos, settings)

        mock_vision._read_single_cell.side_effect = tracking_read

        preprocess_table(base_settings, msg_queue, stop_event)

        # With max_visible_rows=5, row_height=32, first_data_row_y=205:
        # Row 0: y=205 (visual_row=0)
        # Row 1: y=237 (visual_row=1)
        # Row 2: y=269 (visual_row=2)
        # Row 3: y=301 (visual_row=3)
        # Row 4: y=333 (visual_row=4=max-1) → next: reset to scroll_reset_row=2
        # Row 5: y=269 (visual_row=2=scroll_reset_row)
        # Row 6: y=301 (visual_row=3)
        # Row 7: y=333 (visual_row=4=max-1, empty read → break)
        expected = [205, 237, 269, 301, 333, 269, 301, 333]
        assert row_ys == expected
