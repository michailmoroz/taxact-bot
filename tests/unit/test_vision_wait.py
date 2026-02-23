"""Unit tests for vision.wait_for_element() and find_element() retry_count."""

import pytest
from unittest.mock import patch, MagicMock

from clickbot import vision


class TestFindElementRetryCount:
    """Tests for retry_count parameter on find_element()."""

    @patch("clickbot.vision.take_screenshot")
    @patch("clickbot.vision.load_template")
    def test_default_retry_count_from_config(self, mock_load, mock_screenshot):
        """find_element uses config retry_count when not specified."""
        mock_load.return_value = MagicMock(shape=(10, 10, 3))
        mock_screenshot.return_value = MagicMock()

        with patch("clickbot.vision.cv2.matchTemplate") as mock_match:
            mock_match.return_value = MagicMock()
            with patch("clickbot.vision.cv2.minMaxLoc") as mock_loc:
                mock_loc.return_value = (0, 0.5, (0, 0), (0, 0))  # Below threshold

                vision._config["retry_count"] = 3
                vision._config["retry_delay_ms"] = 0

                result = vision.find_element("test.png")

                assert result is None
                assert mock_screenshot.call_count == 3

    @patch("clickbot.vision.take_screenshot")
    @patch("clickbot.vision.load_template")
    def test_custom_retry_count_overrides_config(self, mock_load, mock_screenshot):
        """find_element uses specified retry_count over config."""
        mock_load.return_value = MagicMock(shape=(10, 10, 3))
        mock_screenshot.return_value = MagicMock()

        with patch("clickbot.vision.cv2.matchTemplate") as mock_match:
            mock_match.return_value = MagicMock()
            with patch("clickbot.vision.cv2.minMaxLoc") as mock_loc:
                mock_loc.return_value = (0, 0.5, (0, 0), (0, 0))

                vision._config["retry_count"] = 5
                vision._config["retry_delay_ms"] = 0

                result = vision.find_element("test.png", retry_count=1)

                assert result is None
                assert mock_screenshot.call_count == 1


class TestWaitForElement:
    """Tests for wait_for_element()."""

    @patch("clickbot.vision.find_element")
    def test_found_on_first_poll(self, mock_find):
        """Returns immediately when element found on first check."""
        mock_find.return_value = (100, 200)

        result = vision.wait_for_element("test.png", timeout=5.0, poll_interval=0.01)

        assert result == (100, 200)
        assert mock_find.call_count == 1
        mock_find.assert_called_with(
            "test.png", None, fallback_coords=None, region=None, retry_count=1
        )

    @patch("clickbot.vision.find_element")
    def test_found_after_multiple_polls(self, mock_find):
        """Returns after element appears on Nth poll."""
        mock_find.side_effect = [None, None, (150, 250)]

        result = vision.wait_for_element("test.png", timeout=5.0, poll_interval=0.01)

        assert result == (150, 250)
        assert mock_find.call_count == 3

    @patch("clickbot.vision.find_element")
    def test_timeout_returns_none(self, mock_find):
        """Returns None when timeout expires."""
        mock_find.return_value = None

        result = vision.wait_for_element("test.png", timeout=0.05, poll_interval=0.01)

        assert result is None
        assert mock_find.call_count >= 1

    @patch("clickbot.vision.find_element")
    def test_no_fallback_coords(self, mock_find):
        """wait_for_element never passes fallback_coords."""
        mock_find.return_value = (10, 20)

        vision.wait_for_element("test.png", timeout=1.0, poll_interval=0.01)

        for call in mock_find.call_args_list:
            assert call.kwargs.get("fallback_coords") is None or call[1].get("fallback_coords") is None

    @patch("clickbot.vision.find_element")
    def test_passes_confidence_and_region(self, mock_find):
        """Confidence and region are forwarded to find_element."""
        mock_find.return_value = (10, 20)

        vision.wait_for_element(
            "test.png", timeout=1.0, poll_interval=0.01,
            confidence=0.9, region=(0, 0, 100, 100)
        )

        mock_find.assert_called_with(
            "test.png", 0.9, fallback_coords=None,
            region=(0, 0, 100, 100), retry_count=1
        )
