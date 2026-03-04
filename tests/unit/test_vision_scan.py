"""Unit tests for vision._read_single_cell() and optimized _scan_visible_clients()."""

import pytest
from unittest.mock import patch, call

from clickbot import vision
from clickbot.vision import ClientRow


# Shared test fixtures
SETTINGS = {
    "client_table": {
        "row_height": 32,
        "header_row_y": 145,
        "first_data_row_y": 202,
        "max_visible_rows": 20,
        "columns": {
            "client_name": {"x": 20, "width": 330},
            "return_type": {"x": 470, "width": 55},
            "fed_ef_status": {"x": 700, "width": 117},
        },
    }
}

# Column positions as returned by get_column_positions()
# (center_x, template_width) — return_type key removed (no longer scanned)
COLUMN_POSITIONS = {
    "client_name": (100, 80),
    "fed_ef_status": (730, 90),
}


class TestReadSingleCell:
    """Tests for _read_single_cell()."""

    @patch("clickbot.vision.read_text_region")
    def test_reads_correct_region(self, mock_ocr):
        """_read_single_cell computes cell region from column positions."""
        mock_ocr.return_value = "SMITH LLC"

        result = vision._read_single_cell(
            "client_name", row_y=202, column_positions=COLUMN_POSITIONS, settings=SETTINGS
        )

        assert result == "SMITH LLC"
        # cell_x = center_x - template_w // 2 - 5 = 100 - 40 - 5 = 55
        # col_width from settings = 330
        mock_ocr.assert_called_once_with(55, 202, 330, 32, preprocess=False)

    @patch("clickbot.vision.read_text_region")
    def test_returns_first_nonempty_line(self, mock_ocr):
        """Strips whitespace and returns first non-empty line."""
        mock_ocr.return_value = "\n  Ext: Accepted  \n\n"

        result = vision._read_single_cell(
            "fed_ef_status", row_y=234, column_positions=COLUMN_POSITIONS, settings=SETTINGS
        )

        assert result == "Ext: Accepted"

    @patch("clickbot.vision.read_text_region")
    def test_returns_empty_string_for_blank(self, mock_ocr):
        """Returns empty string when OCR returns whitespace only."""
        mock_ocr.return_value = "  \n  \n  "

        result = vision._read_single_cell(
            "fed_ef_status", row_y=234, column_positions=COLUMN_POSITIONS, settings=SETTINGS
        )

        assert result == ""


class TestScanVisibleClientsOptimized:
    """Tests for optimized _scan_visible_clients() read order."""

    @patch("clickbot.vision._read_single_cell")
    def test_skips_nonempty_status_row(self, mock_read):
        """Rows with non-empty fed_ef_status are skipped quickly."""
        # Row 0: status="Ext: Accepted", name="SMITH LLC"
        # Row 1: empty name → end of table
        mock_read.side_effect = [
            "Ext: Accepted",  # row 0: fed_ef_status
            "SMITH LLC",      # row 0: client_name (for scroll tracking)
            "",               # row 1: fed_ef_status
            "",               # row 1: client_name → empty → break
        ]

        settings = {**SETTINGS, "client_table": {**SETTINGS["client_table"], "max_visible_rows": 2}}
        result = vision._scan_visible_clients(settings, COLUMN_POSITIONS, selected_return_type="1120S")

        row_data, click_pos, last_client = result
        assert row_data is None
        assert last_client == "SMITH LLC"
        # return_type was never read (no OCR for that column)
        col_names = [c.args[0] for c in mock_read.call_args_list]
        assert "return_type" not in col_names

    @patch("clickbot.vision._read_single_cell")
    def test_sets_return_type_from_parameter(self, mock_read):
        """ClientRow.return_type is set from selected_return_type, not OCR."""
        # Row 0: status empty, name="NEW CLIENT" — no return_type OCR call
        mock_read.side_effect = [
            "",             # row 0: fed_ef_status (empty!)
            "NEW CLIENT",   # row 0: client_name
        ]

        settings = {**SETTINGS, "client_table": {**SETTINGS["client_table"], "max_visible_rows": 1}}
        result = vision._scan_visible_clients(
            settings, COLUMN_POSITIONS, selected_return_type="1120S"
        )

        row_data, click_pos, last_client = result
        assert row_data is not None
        assert row_data.client_name == "NEW CLIENT"
        assert row_data.return_type == "1120S"  # from parameter, not OCR
        assert row_data.fed_ef_status == ""
        assert mock_read.call_count == 2  # only fed_ef_status + client_name

    @patch("clickbot.vision._read_single_cell")
    def test_selected_return_type_propagated_to_client_row(self, mock_read):
        """Different selected_return_type values are correctly reflected in ClientRow."""
        mock_read.side_effect = [
            "",          # fed_ef_status empty
            "CORP INC",  # client_name
        ]

        settings = {**SETTINGS, "client_table": {**SETTINGS["client_table"], "max_visible_rows": 1}}
        result = vision._scan_visible_clients(
            settings, COLUMN_POSITIONS, selected_return_type="1040"
        )

        row_data, _, _ = result
        assert row_data is not None
        assert row_data.return_type == "1040"

    @patch("clickbot.vision._read_single_cell")
    def test_skips_processed_client_with_two_reads(self, mock_read):
        """Already-processed clients with empty status need only 2 OCR calls."""
        # Row 0: status empty, name="DONE CLIENT" (already processed)
        # Row 1: empty name → end of table
        mock_read.side_effect = [
            "",              # row 0: fed_ef_status (empty)
            "DONE CLIENT",   # row 0: client_name
            "",              # row 1: fed_ef_status (empty)
            "",              # row 1: client_name → empty → break
        ]

        settings = {**SETTINGS, "client_table": {**SETTINGS["client_table"], "max_visible_rows": 2}}
        result = vision._scan_visible_clients(
            settings, COLUMN_POSITIONS,
            processed_clients={"DONE CLIENT"},
            selected_return_type="1120"
        )

        row_data, click_pos, last_client = result
        assert row_data is None
        # return_type was never read for "DONE CLIENT"
        col_names = [c.args[0] for c in mock_read.call_args_list]
        assert col_names == ["fed_ef_status", "client_name", "fed_ef_status", "client_name"]

    @patch("clickbot.vision._read_single_cell")
    def test_mixed_rows_optimized(self, mock_read):
        """Mix of filed, processed, and candidate rows uses minimal OCR (2 cols only)."""
        mock_read.side_effect = [
            "Accepted",     # row 0: fed_ef_status (filed)
            "CLIENT A",     # row 0: client_name (scroll tracking)
            "Ext: Accepted",  # row 1: fed_ef_status (filed)
            "CLIENT B",     # row 1: client_name (scroll tracking)
            "",             # row 2: fed_ef_status (empty!)
            "CLIENT C",     # row 2: client_name (processed)
            "",             # row 3: fed_ef_status (empty!)
            "CLIENT D",     # row 3: client_name (new!) → match
        ]

        settings = {**SETTINGS, "client_table": {**SETTINGS["client_table"], "max_visible_rows": 4}}
        result = vision._scan_visible_clients(
            settings, COLUMN_POSITIONS,
            processed_clients={"CLIENT C"},
            selected_return_type="1120"
        )

        row_data, click_pos, last_client = result
        assert row_data is not None
        assert row_data.client_name == "CLIENT D"
        assert row_data.return_type == "1120"  # from parameter
        # Total: 8 OCR calls (2 cols × 4 rows) — no return_type column
        assert mock_read.call_count == 8
