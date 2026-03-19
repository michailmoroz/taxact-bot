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
# (center_x, template_width)
COLUMN_POSITIONS = {
    "client_name": (100, 80),
    "return_type": (490, 55),
    "fed_ef_status": (730, 90),
}


class TestGetColumnPositionsExtraColumns:
    """Tests for get_column_positions() extra_columns parameter."""

    @patch("clickbot.vision.load_template")
    @patch("clickbot.vision.find_element")
    def test_without_extra_columns(self, mock_find, mock_load):
        """get_column_positions() without extra_columns finds 3 standard columns."""
        mock_find.return_value = (500, 100)
        mock_template = type("MockTemplate", (), {"shape": (30, 80)})()
        mock_load.return_value = mock_template

        result = vision.get_column_positions()

        assert result is not None
        assert len(result) == 3
        assert "client_name" in result
        assert "return_type" in result
        assert "fed_ef_status" in result
        assert "ssn_ein" not in result

    @patch("clickbot.vision.load_template")
    @patch("clickbot.vision.find_element")
    def test_with_ssn_ein_extra_column(self, mock_find, mock_load):
        """get_column_positions(extra_columns=["ssn_ein"]) finds 4 columns."""
        mock_find.return_value = (500, 100)
        mock_template = type("MockTemplate", (), {"shape": (30, 80)})()
        mock_load.return_value = mock_template

        result = vision.get_column_positions(extra_columns=["ssn_ein"])

        assert result is not None
        assert len(result) == 4
        assert "ssn_ein" in result

    @patch("clickbot.vision.load_template")
    @patch("clickbot.vision.find_element")
    def test_extra_column_not_found_returns_none(self, mock_find, mock_load):
        """get_column_positions returns None if extra column header not found."""
        def find_side_effect(template_path, confidence=0.7, fallback_coords=None):
            if "ssn_ein" in template_path:
                return None  # SSN/EIN not found
            return (500, 100)

        mock_find.side_effect = find_side_effect
        mock_template = type("MockTemplate", (), {"shape": (30, 80)})()
        mock_load.return_value = mock_template

        result = vision.get_column_positions(extra_columns=["ssn_ein"])
        assert result is None  # Hard error

    @patch("clickbot.vision.load_template")
    @patch("clickbot.vision.find_element")
    def test_unknown_extra_column_ignored(self, mock_find, mock_load):
        """Unknown extra column names are silently ignored."""
        mock_find.return_value = (500, 100)
        mock_template = type("MockTemplate", (), {"shape": (30, 80)})()
        mock_load.return_value = mock_template

        result = vision.get_column_positions(extra_columns=["nonexistent_col"])

        assert result is not None
        assert len(result) == 3  # Only standard 3 columns


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
        # Fixed x from settings (x=20), col_width from settings = 330
        mock_ocr.assert_called_once_with(20, 202, 330, 32, preprocess=False)

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

    @patch("clickbot.vision.normalize_return_type", return_value="1120S")
    @patch("clickbot.vision._read_single_cell")
    def test_sets_return_type_from_parameter(self, mock_read, mock_norm):
        """ClientRow.return_type is set from selected_return_type (GUI), not OCR value."""
        # Row 0: status empty, name="NEW CLIENT", return_type OCR matches selected
        mock_read.side_effect = [
            "",             # row 0: fed_ef_status (empty!)
            "NEW CLIENT",   # row 0: client_name
            "1120S",        # row 0: return_type (OCR — matches selected)
        ]

        settings = {**SETTINGS, "client_table": {**SETTINGS["client_table"], "max_visible_rows": 1}}
        result = vision._scan_visible_clients(
            settings, COLUMN_POSITIONS, selected_return_type="1120S"
        )

        row_data, click_pos, last_client = result
        assert row_data is not None
        assert row_data.client_name == "NEW CLIENT"
        assert row_data.return_type == "1120S"  # from GUI parameter
        assert row_data.fed_ef_status == ""
        assert mock_read.call_count == 3  # fed_ef_status + client_name + return_type

    @patch("clickbot.vision.normalize_return_type", return_value="1120S")
    @patch("clickbot.vision._read_single_cell")
    def test_skips_client_with_wrong_return_type(self, mock_read, mock_norm):
        """Clients whose OCR return_type doesn't match selected_return_type are skipped."""
        # Row 0: status empty, name="SCORP INC", but return_type is 1120S (not 1120)
        # Row 1: empty name → end of table
        mock_read.side_effect = [
            "",           # row 0: fed_ef_status (empty)
            "SCORP INC",  # row 0: client_name
            "1120S",      # row 0: return_type (OCR — does NOT match selected "1120")
            "",           # row 1: fed_ef_status
            "",           # row 1: client_name → empty → break
        ]

        settings = {**SETTINGS, "client_table": {**SETTINGS["client_table"], "max_visible_rows": 2}}
        result = vision._scan_visible_clients(
            settings, COLUMN_POSITIONS,
            selected_return_type="1120"  # user selected 1120, but client is 1120S
        )

        row_data, _, _ = result
        assert row_data is None  # client was skipped

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

    @patch("clickbot.vision.normalize_return_type", return_value="1120")
    @patch("clickbot.vision._read_single_cell")
    def test_mixed_rows_optimized(self, mock_read, mock_norm):
        """Mix of filed, processed, and candidate rows uses minimal OCR."""
        mock_read.side_effect = [
            "Accepted",       # row 0: fed_ef_status (filed)
            "CLIENT A",       # row 0: client_name (scroll tracking)
            "Ext: Accepted",  # row 1: fed_ef_status (filed)
            "CLIENT B",       # row 1: client_name (scroll tracking)
            "",               # row 2: fed_ef_status (empty!)
            "CLIENT C",       # row 2: client_name (processed → skip)
            "",               # row 3: fed_ef_status (empty!)
            "CLIENT D",       # row 3: client_name (new!)
            "1120",           # row 3: return_type (candidate → matches)
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
        assert row_data.return_type == "1120"  # from GUI parameter
        # Total: 9 OCR calls (filed rows: 2 each, processed: 2, candidate: 3)
        assert mock_read.call_count == 9
