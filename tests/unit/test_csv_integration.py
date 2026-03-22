"""Unit tests for Phase 10b-2: CSV integration in bot loop."""

import csv
import inspect
import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from clickbot.vision import ClientRow
from clickbot.bot_controller import BotController
from clickbot.preprocessor import ClientRecord


# ── ClientRow.client_id Tests ─────────────────────────────────────────


class TestClientRowClientId:
    """Tests for client_id field on ClientRow."""

    def test_client_id_defaults_to_empty(self):
        r = ClientRow(0, 0, "Test Inc", "1040", "")
        assert r.client_id == ""

    def test_client_id_set_by_keyword(self):
        r = ClientRow(0, 0, "Test Inc", "1040", "", client_id="12-3456789")
        assert r.client_id == "12-3456789"

    def test_existing_fields_unchanged(self):
        r = ClientRow(0, 100, "SMITH LLC", "1120S", "Submitted", client_id="98-7654321")
        assert r.row_index == 0
        assert r.y_position == 100
        assert r.client_name == "SMITH LLC"
        assert r.return_type == "1120S"
        assert r.fed_ef_status == "Submitted"
        assert r.client_id == "98-7654321"


# ── BotController csv_path Tests ──────────────────────────────────────


class TestBotControllerCsvPath:
    """Tests for csv_path parameter on BotController."""

    def test_accepts_csv_path_parameter(self):
        sig = inspect.signature(BotController.__init__)
        assert "csv_path" in sig.parameters

    def test_csv_path_defaults_to_none(self):
        bc = BotController({"display": {}}, selected_return_type="1040")
        assert bc.csv_path is None

    def test_csv_path_stored(self, tmp_path):
        csv_file = tmp_path / "clients.csv"
        csv_file.write_text("Client,ID,Return Type,Status\n")
        bc = BotController({"display": {}}, selected_return_type="1040", csv_path=csv_file)
        assert bc.csv_path == csv_file


# ── find_next_client signature Tests ──────────────────────────────────


class TestFindNextClientSignature:
    """Tests for find_next_client csv_records parameter."""

    def test_accepts_csv_records_parameter(self):
        from clickbot.vision import find_next_client
        sig = inspect.signature(find_next_client)
        assert "csv_records" in sig.parameters

    def test_csv_records_defaults_to_none(self):
        from clickbot.vision import find_next_client
        sig = inspect.signature(find_next_client)
        assert sig.parameters["csv_records"].default is None


# ── _scan_visible_clients CSV logic Tests ─────────────────────────────


class TestScanVisibleClientsCsv:
    """Tests for CSV-based skip logic in _scan_visible_clients."""

    @patch("clickbot.vision._read_single_cell")
    def test_skips_non_todo_csv_client(self, mock_read):
        """Client with non-TODO CSV status is skipped."""
        from clickbot.vision import _scan_visible_clients

        # Row 0: empty status, client_name "SMITH", ssn "12-345", return_type "1040"
        # But CSV has this client as "Submitted" -> should skip
        mock_read.side_effect = [
            "",          # fed_ef_status (empty -> candidate)
            "SMITH LLC", # client_name
            "12-345",    # ssn_ein
        ]

        csv_records = [
            ClientRecord("SMITH LLC", "12-345", "1040", "Submitted"),
        ]
        col_positions = {
            "fed_ef_status": (800, 100),
            "client_name": (200, 100),
            "ssn_ein": (400, 100),
            "return_type": (600, 100),
        }
        settings = {"client_table": {
            "first_data_row_y": 170, "row_height": 25, "max_visible_rows": 1,
            "columns": {
                "fed_ef_status": {"x": 800, "width": 100},
                "client_name": {"x": 200, "width": 100},
                "ssn_ein": {"x": 400, "width": 100},
                "return_type": {"x": 600, "width": 100},
            }
        }}

        result = _scan_visible_clients(
            settings, col_positions, selected_return_type="1040",
            csv_records=csv_records
        )

        # Should return no match (None, None, last_client)
        assert result[0] is None

    @patch("clickbot.vision._read_single_cell")
    def test_finds_todo_csv_client(self, mock_read):
        """Client with TODO CSV status is returned."""
        from clickbot.vision import _scan_visible_clients

        # Row 0: empty status, client "JONES", ssn "98-765", type "1040"
        mock_read.side_effect = [
            "",          # fed_ef_status
            "JONES INC", # client_name
            "98-765",    # ssn_ein
            "1040",      # return_type (OCR)
        ]

        csv_records = [
            ClientRecord("JONES INC", "98-765", "1040", "TODO"),
        ]
        col_positions = {
            "fed_ef_status": (800, 100),
            "client_name": (200, 100),
            "ssn_ein": (400, 100),
            "return_type": (600, 100),
        }
        settings = {"client_table": {
            "first_data_row_y": 170, "row_height": 25, "max_visible_rows": 1,
            "columns": {
                "fed_ef_status": {"x": 800, "width": 100},
                "client_name": {"x": 200, "width": 100},
                "ssn_ein": {"x": 400, "width": 100},
                "return_type": {"x": 600, "width": 100},
            }
        }}

        result = _scan_visible_clients(
            settings, col_positions, selected_return_type="1040",
            csv_records=csv_records
        )

        row_data, click_pos, last_name = result
        assert row_data is not None
        assert row_data.client_name == "JONES INC"
        assert row_data.client_id == "98-765"

    @patch("clickbot.vision._read_single_cell")
    def test_auto_status_update_collected(self, mock_read):
        """Auto-update collected when TaxAct status differs from CSV."""
        from clickbot.vision import _scan_visible_clients

        # Row 0: non-empty status "Ext. Accepted"
        mock_read.side_effect = [
            "Ext. Accepted",  # fed_ef_status (non-empty -> skip)
            "SMITH LLC",       # client_name (for scroll tracking)
            "12-345",          # ssn_ein (for auto-update)
        ]

        csv_records = [
            ClientRecord("SMITH LLC", "12-345", "1040", "Submitted"),
        ]
        col_positions = {
            "fed_ef_status": (800, 100),
            "client_name": (200, 100),
            "ssn_ein": (400, 100),
            "return_type": (600, 100),
        }
        settings = {"client_table": {
            "first_data_row_y": 170, "row_height": 25, "max_visible_rows": 1,
            "columns": {
                "fed_ef_status": {"x": 800, "width": 100},
                "client_name": {"x": 200, "width": 100},
                "ssn_ein": {"x": 400, "width": 100},
                "return_type": {"x": 600, "width": 100},
            }
        }}

        status_updates = []
        _scan_visible_clients(
            settings, col_positions, selected_return_type="1040",
            csv_records=csv_records, status_updates=status_updates
        )

        assert len(status_updates) == 1
        assert status_updates[0] == ("SMITH LLC", "12-345", "1040", "Ext. Accepted")

    @patch("clickbot.vision._read_single_cell")
    def test_no_auto_update_when_status_matches(self, mock_read):
        """No auto-update when TaxAct status equals CSV status."""
        from clickbot.vision import _scan_visible_clients

        mock_read.side_effect = [
            "Submitted",   # fed_ef_status
            "SMITH LLC",   # client_name
            "12-345",      # ssn_ein
        ]

        csv_records = [
            ClientRecord("SMITH LLC", "12-345", "1040", "Submitted"),
        ]
        col_positions = {
            "fed_ef_status": (800, 100),
            "client_name": (200, 100),
            "ssn_ein": (400, 100),
        }
        settings = {"client_table": {
            "first_data_row_y": 170, "row_height": 25, "max_visible_rows": 1,
            "columns": {
                "fed_ef_status": {"x": 800, "width": 100},
                "client_name": {"x": 200, "width": 100},
                "ssn_ein": {"x": 400, "width": 100},
            }
        }}

        status_updates = []
        _scan_visible_clients(
            settings, col_positions, selected_return_type="1040",
            csv_records=csv_records, status_updates=status_updates
        )

        assert len(status_updates) == 0

    @patch("clickbot.vision._read_single_cell")
    def test_backward_compat_without_csv(self, mock_read):
        """Without csv_records, uses processed_clients set (backward-compat)."""
        from clickbot.vision import _scan_visible_clients

        # Row 0: empty status, client "SMITH" - but in processed_clients
        mock_read.side_effect = [
            "",          # fed_ef_status
            "SMITH LLC", # client_name
        ]

        col_positions = {
            "fed_ef_status": (800, 100),
            "client_name": (200, 100),
        }
        settings = {"client_table": {
            "first_data_row_y": 170, "row_height": 25, "max_visible_rows": 1,
            "columns": {
                "fed_ef_status": {"x": 800, "width": 100},
                "client_name": {"x": 200, "width": 100},
            }
        }}

        result = _scan_visible_clients(
            settings, col_positions,
            processed_clients={"SMITH LLC"},
            selected_return_type="1040",
            csv_records=None
        )

        assert result[0] is None  # Skipped because in processed_clients


# ── CSV Status Write Tests (via bot_controller) ──────────────────────


class TestCsvStatusWrites:
    """Tests for CSV status updates after processing."""

    def _create_csv(self, tmp_path, records):
        """Helper: create a CSV with given records."""
        csv_file = tmp_path / "clients.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Client", "ID", "Return Type", "Status"])
            writer.writeheader()
            for r in records:
                writer.writerow({
                    "Client": r.client_name,
                    "ID": r.client_id,
                    "Return Type": r.return_type,
                    "Status": r.status,
                })
        return csv_file

    def _read_csv_status(self, csv_file, client_name):
        """Helper: read status for a client from CSV."""
        from clickbot.preprocessor import load_csv
        records = load_csv(csv_file)
        for r in records:
            if r.client_name == client_name:
                return r.status
        return None

    def test_successful_client_writes_submitted(self, tmp_path):
        """Successful processing writes 'Submitted' to CSV."""
        from clickbot.preprocessor import update_client_status

        csv_file = self._create_csv(tmp_path, [
            ClientRecord("TEST INC", "12-345", "1040", "TODO"),
        ])

        update_client_status(csv_file, "TEST INC", "12-345", "1040", "Submitted")

        assert self._read_csv_status(csv_file, "TEST INC") == "Submitted"

    def test_abort_reason_written_to_csv(self, tmp_path):
        """Abort reason is written directly to CSV status."""
        from clickbot.preprocessor import update_client_status

        csv_file = self._create_csv(tmp_path, [
            ClientRecord("FAIL INC", "98-765", "1040", "TODO"),
        ])

        update_client_status(csv_file, "FAIL INC", "98-765", "1040", "FAIL: Wizard (Stage 12)")

        assert self._read_csv_status(csv_file, "FAIL INC") == "FAIL: Wizard (Stage 12)"

    def test_generic_error_writes_fail_prefix(self, tmp_path):
        """Generic errors get FAIL: prefix."""
        from clickbot.preprocessor import update_client_status

        csv_file = self._create_csv(tmp_path, [
            ClientRecord("ERR INC", "11-222", "1040", "TODO"),
        ])

        update_client_status(csv_file, "ERR INC", "11-222", "1040", "FAIL: Step failed: click_efile_menu")

        status = self._read_csv_status(csv_file, "ERR INC")
        assert status.startswith("FAIL:")

    def test_other_records_preserved(self, tmp_path):
        """Updating one record preserves others."""
        from clickbot.preprocessor import update_client_status

        csv_file = self._create_csv(tmp_path, [
            ClientRecord("AAA INC", "11-111", "1040", "TODO"),
            ClientRecord("BBB INC", "22-222", "1040", "TODO"),
            ClientRecord("CCC INC", "33-333", "1120S", "Submitted"),
        ])

        update_client_status(csv_file, "AAA INC", "11-111", "1040", "Submitted")

        assert self._read_csv_status(csv_file, "AAA INC") == "Submitted"
        assert self._read_csv_status(csv_file, "BBB INC") == "TODO"
        assert self._read_csv_status(csv_file, "CCC INC") == "Submitted"


# ── GUI Status Count Tests ────────────────────────────────────────────


class TestGuiStatusCounts:
    """Tests for updated CSV status counting logic."""

    def test_count_new_status_values(self):
        """Counts handle Submitted, FAIL: ..., and other status values."""
        records = [
            ClientRecord("A", "", "1040", "TODO"),
            ClientRecord("B", "", "1040", "Submitted"),
            ClientRecord("C", "", "1040", "FAIL: Wizard (Stage 12)"),
            ClientRecord("D", "", "1040", "FAIL: Alerts not passed"),
            ClientRecord("E", "", "1040", "Ext. Accepted"),
        ]

        todo = sum(1 for r in records if r.status == "TODO")
        fail = sum(1 for r in records if r.status.startswith("FAIL"))
        done = len(records) - todo - fail

        assert todo == 1
        assert fail == 2
        assert done == 2  # Submitted + Ext. Accepted


# ── Backward Compatibility Tests ──────────────────────────────────────


class TestBackwardCompatibility:
    """Tests ensuring in-memory tracking still works without CSV."""

    def test_bot_controller_no_csv(self):
        """BotController without csv_path uses in-memory tracking."""
        bc = BotController({"display": {}}, selected_return_type="1040")
        assert bc.csv_path is None

    @patch("clickbot.vision.get_column_positions")
    def test_find_next_client_returns_old_format_without_csv(self, mock_cols):
        """find_next_client without csv_records returns (ClientRow, pos) or None."""
        mock_cols.return_value = None  # Simulate no Client Manager screen

        from clickbot.vision import find_next_client
        result = find_next_client({"loop": {}}, selected_return_type="1040")

        # Should return None (not a tuple with status_updates)
        assert result is None

    @patch("clickbot.vision.get_column_positions")
    def test_find_next_client_returns_new_format_with_csv(self, mock_cols):
        """find_next_client with csv_records returns (result, status_updates)."""
        mock_cols.return_value = None  # Simulate no Client Manager screen

        from clickbot.vision import find_next_client
        result = find_next_client(
            {"loop": {}}, selected_return_type="1040",
            csv_records=[]
        )

        # Should return (None, []) tuple
        assert isinstance(result, tuple)
        assert result[0] is None
        assert result[1] == []
