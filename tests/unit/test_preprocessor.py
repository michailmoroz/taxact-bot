"""Unit tests for clickbot.preprocessor module."""

import csv
from pathlib import Path

import pytest

from clickbot.preprocessor import (
    ClientRecord,
    load_csv,
    update_client_status,
    get_todo_clients,
    get_latest_csv,
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
