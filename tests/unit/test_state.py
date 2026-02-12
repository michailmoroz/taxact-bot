"""Unit tests for clickbot.state module."""

import pytest
from clickbot.state import ClientTracker


class TestClientTracker:
    """Tests for ClientTracker class."""

    def test_initial_state_empty(self):
        """New tracker should have no processed clients."""
        tracker = ClientTracker()
        assert tracker.get_count() == 0
        assert not tracker.is_processed("ANY_CLIENT")

    def test_mark_processed(self):
        """Marking a client should add it to processed set."""
        tracker = ClientTracker()
        tracker.mark_processed("SANDMEYER INC")

        assert tracker.is_processed("SANDMEYER INC")
        assert tracker.get_count() == 1

    def test_mark_multiple_clients(self):
        """Multiple clients can be marked as processed."""
        tracker = ClientTracker()
        tracker.mark_processed("CLIENT_A")
        tracker.mark_processed("CLIENT_B")
        tracker.mark_processed("CLIENT_C")

        assert tracker.is_processed("CLIENT_A")
        assert tracker.is_processed("CLIENT_B")
        assert tracker.is_processed("CLIENT_C")
        assert tracker.get_count() == 3

    def test_mark_same_client_twice(self):
        """Marking same client twice should not increase count."""
        tracker = ClientTracker()
        tracker.mark_processed("DUPLICATE")
        tracker.mark_processed("DUPLICATE")

        assert tracker.get_count() == 1

    def test_is_processed_case_sensitive(self):
        """Client name matching should be case-sensitive."""
        tracker = ClientTracker()
        tracker.mark_processed("Client Name")

        assert tracker.is_processed("Client Name")
        assert not tracker.is_processed("CLIENT NAME")
        assert not tracker.is_processed("client name")

    def test_clear(self):
        """Clear should remove all processed clients."""
        tracker = ClientTracker()
        tracker.mark_processed("CLIENT_1")
        tracker.mark_processed("CLIENT_2")
        assert tracker.get_count() == 2

        tracker.clear()

        assert tracker.get_count() == 0
        assert not tracker.is_processed("CLIENT_1")
        assert not tracker.is_processed("CLIENT_2")

    def test_processed_set_accessible(self):
        """The processed set should be directly accessible."""
        tracker = ClientTracker()
        tracker.mark_processed("TEST")

        # Used by vision.find_next_client()
        assert "TEST" in tracker.processed
        assert len(tracker.processed) == 1
