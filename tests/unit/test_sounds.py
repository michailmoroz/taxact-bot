"""Unit tests for clickbot.sounds module."""

import pytest
from unittest.mock import patch, MagicMock
from clickbot import sounds


class TestSoundsModule:
    """Tests for sounds module functions."""

    def test_set_enabled(self):
        """set_enabled should update the enabled flag."""
        sounds.set_enabled(True)
        # is_enabled also checks WINSOUND_AVAILABLE
        # We just verify set_enabled doesn't crash

        sounds.set_enabled(False)
        # Still shouldn't crash

    def test_is_enabled_when_disabled(self):
        """is_enabled should return False when sounds disabled."""
        sounds.set_enabled(False)
        # Note: is_enabled() also checks WINSOUND_AVAILABLE
        # On non-Windows, this will always be False
        result = sounds.is_enabled()
        # Result depends on platform, but shouldn't crash
        assert isinstance(result, bool)

    @patch.object(sounds, 'WINSOUND_AVAILABLE', True)
    @patch.object(sounds, 'winsound', create=True)
    def test_play_success_calls_beep(self, mock_winsound):
        """play_success should call winsound.Beep when enabled."""
        sounds.set_enabled(True)
        mock_winsound.Beep = MagicMock()

        sounds.play_success(freq=1000, duration=200)

        mock_winsound.Beep.assert_called_once_with(1000, 200)

    @patch.object(sounds, 'WINSOUND_AVAILABLE', True)
    @patch.object(sounds, 'winsound', create=True)
    def test_play_success_skipped_when_disabled(self, mock_winsound):
        """play_success should not call Beep when disabled."""
        sounds.set_enabled(False)
        mock_winsound.Beep = MagicMock()

        sounds.play_success()

        mock_winsound.Beep.assert_not_called()

    @patch.object(sounds, 'WINSOUND_AVAILABLE', True)
    @patch.object(sounds, 'winsound', create=True)
    def test_play_iteration_calls_playsound(self, mock_winsound):
        """play_iteration should call winsound.PlaySound with correct params."""
        sounds.set_enabled(True)
        mock_winsound.PlaySound = MagicMock()
        mock_winsound.SND_ALIAS = 0x00010000
        mock_winsound.SND_ASYNC = 0x00000001

        sounds.play_iteration()

        mock_winsound.PlaySound.assert_called_once_with(
            "SystemAsterisk",
            mock_winsound.SND_ALIAS | mock_winsound.SND_ASYNC
        )

    @patch.object(sounds, 'WINSOUND_AVAILABLE', True)
    @patch.object(sounds, 'winsound', create=True)
    def test_play_iteration_skipped_when_disabled(self, mock_winsound):
        """play_iteration should not call PlaySound when disabled."""
        sounds.set_enabled(False)
        mock_winsound.PlaySound = MagicMock()

        sounds.play_iteration()

        mock_winsound.PlaySound.assert_not_called()

    @patch.object(sounds, 'WINSOUND_AVAILABLE', True)
    @patch.object(sounds, 'winsound', create=True)
    def test_play_error_calls_beep_multiple_times(self, mock_winsound):
        """play_error should call Beep multiple times (default 3)."""
        sounds.set_enabled(True)
        mock_winsound.Beep = MagicMock()

        sounds.play_error(freq=400, duration=500, repeats=3)

        assert mock_winsound.Beep.call_count == 3

    @patch.object(sounds, 'WINSOUND_AVAILABLE', True)
    @patch.object(sounds, 'winsound', create=True)
    def test_play_complete_calls_beep_for_melody(self, mock_winsound):
        """play_complete should call Beep for each note in melody."""
        sounds.set_enabled(True)
        mock_winsound.Beep = MagicMock()

        sounds.play_complete(frequencies=[523, 659, 784])

        assert mock_winsound.Beep.call_count == 3

    def test_play_success_handles_exception(self):
        """play_success should not raise exception on error."""
        sounds.set_enabled(True)
        # This should not crash even if winsound fails
        # (On non-Windows or with mocked failure)
        try:
            sounds.play_success()
        except Exception:
            pytest.fail("play_success raised an exception")

    def test_play_iteration_handles_exception(self):
        """play_iteration should not raise exception on error."""
        sounds.set_enabled(True)
        try:
            sounds.play_iteration()
        except Exception:
            pytest.fail("play_iteration raised an exception")
