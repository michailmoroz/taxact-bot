"""Unit tests for Phase 7: process_executor verification and multi-action."""

import queue
import threading
import pytest
from unittest.mock import patch, MagicMock, call

from clickbot.process_executor import ProcessExecutor, ExecutionResult


@pytest.fixture
def executor():
    """Create a ProcessExecutor with test settings."""
    settings = {
        "vision": {
            "screenshot_base_path": ".agents/screenshots/buttons",
            "confidence_threshold": 0.8,
            "retry_count": 1,
            "retry_delay_ms": 0,
        },
        "timing": {"default_wait": 0.01},
        "validation": {
            "enabled": True,
            "poll_interval_ms": 10,
            "step_timeout_s": 0.1,
            "max_retries": 2,
            "min_wait_after_ms": 10,
            "verify_base_path": "assets/verify",
        },
        "ocr": {},
    }
    msg_queue = queue.Queue()
    stop_event = threading.Event()
    return ProcessExecutor(settings, msg_queue, stop_event)


class TestGetVerifyBasePath:
    """Tests for _get_verify_base_path()."""

    def test_returns_configured_path(self, executor):
        """Returns verify_base_path from settings."""
        result = executor._get_verify_base_path()
        assert result == "assets/verify"


class TestWaitAndVerify:
    """Tests for _wait_and_verify()."""

    @patch("clickbot.process_executor.vision.wait_for_element")
    def test_success_on_first_attempt(self, mock_wait, executor):
        """Returns True when screen verified on first poll."""
        mock_wait.return_value = (100, 200)

        step = {"id": 1, "name": "test_step", "action": "click"}
        cfg = executor.settings["validation"]

        result = executor._wait_and_verify(step, "1120S/test.png", cfg)

        assert result is True
        assert mock_wait.call_count == 1
        # Verify base_path and stop_event are passed through
        mock_wait.assert_called_with(
            "1120S/test.png", timeout=cfg["step_timeout_s"],
            poll_interval=cfg["poll_interval_ms"] / 1000,
            base_path="assets/verify",
            stop_event=executor.stop_event
        )

    @patch("clickbot.process_executor.vision.wait_for_element")
    def test_retry_after_timeout(self, mock_wait, executor):
        """Retries click after timeout, then succeeds."""
        mock_wait.side_effect = [None, (100, 200)]

        step = {"id": 1, "name": "test_step", "action": "click", "target": {"image": "btn.png"}}
        cfg = executor.settings["validation"]

        with patch.object(executor, "_retry_step_click") as mock_retry:
            result = executor._wait_and_verify(step, "1120S/test.png", cfg)

        assert result is True
        assert mock_wait.call_count == 2
        mock_retry.assert_called_once_with(step)

    @patch("clickbot.process_executor.vision.wait_for_element")
    def test_max_retries_returns_false(self, mock_wait, executor):
        """Returns False after all retries exhausted."""
        mock_wait.return_value = None

        step = {"id": 1, "name": "test_step", "action": "click", "target": {"image": "btn.png"}}
        cfg = executor.settings["validation"]

        with patch.object(executor, "_retry_step_click"):
            result = executor._wait_and_verify(step, "1120S/test.png", cfg)

        assert result is False
        # max_retries=2, so 2 attempts
        assert mock_wait.call_count == 2


class TestBackwardCompatibility:
    """Tests for backward compatibility with steps without verify_next."""

    @patch("clickbot.process_executor.load_process")
    @patch("clickbot.process_executor.vision.configure")
    @patch("clickbot.process_executor.vision.configure_tesseract")
    def test_steps_without_verify_next_use_wait_after(self, mock_tess, mock_conf, mock_load, executor):
        """Steps without verify_next fall back to wait_after timing."""
        mock_load.return_value = {
            "name": "Test",
            "return_type": "1120",
            "version": "1.0",
            "steps": [
                {
                    "id": 1,
                    "name": "test_click",
                    "action": "click",
                    "target": {"image": "test.png"},
                    "wait_after": 0.01
                }
            ],
            "static_inputs": {}
        }

        with patch.object(executor, "_execute_step", return_value=True):
            with patch("clickbot.process_executor.time.sleep") as mock_sleep:
                with patch("clickbot.process_executor.vision.find_element"):
                    result = executor.execute("1120")

        assert result.success is True
        # Should have called sleep with wait_after value
        mock_sleep.assert_called_with(0.01)


class TestActionMulti:
    """Tests for _action_multi()."""

    def test_executes_sub_actions_in_sequence(self, executor):
        """Multi action executes all sub-actions."""
        step = {
            "id": 1,
            "name": "multi_test",
            "action": "multi",
            "actions": [
                {"action": "click", "target": {"image": "a.png"}, "wait_after": 0.01},
                {"action": "click", "target": {"image": "b.png"}, "wait_after": 0.01},
            ]
        }

        with patch.object(executor, "_execute_step", return_value=True) as mock_exec:
            result = executor._action_multi(step, {})

        assert result is True
        assert mock_exec.call_count == 2

    def test_stops_on_sub_action_failure(self, executor):
        """Multi action stops if any sub-action fails."""
        step = {
            "id": 1,
            "name": "multi_test",
            "action": "multi",
            "actions": [
                {"action": "click", "target": {"image": "a.png"}, "wait_after": 0.01},
                {"action": "click", "target": {"image": "b.png"}, "wait_after": 0.01},
            ]
        }

        with patch.object(executor, "_execute_step", side_effect=[False]) as mock_exec:
            result = executor._action_multi(step, {})

        assert result is False
        assert mock_exec.call_count == 1


class TestVerifyBranch:
    """Tests for _verify_branch() in conditional steps."""

    @patch("clickbot.process_executor.vision.wait_for_element")
    def test_branch_with_verify_next(self, mock_wait, executor):
        """Branch with verify_next triggers verification."""
        mock_wait.return_value = (100, 200)

        branch = {
            "action": "click",
            "target": {"image": "btn.png"},
            "verify_next": "1120S/06_s_corp_name.png"
        }

        result = executor._verify_branch(branch)

        assert result is True
        mock_wait.assert_called_once()

    def test_branch_without_verify_next(self, executor):
        """Branch without verify_next passes through."""
        branch = {
            "action": "click",
            "target": {"image": "btn.png"}
        }

        result = executor._verify_branch(branch)

        assert result is True


class TestProcessLoaderStages:
    """Tests for process_loader with stages key."""

    def test_load_1120s_with_stages(self):
        """1120S.json with 'stages' key loads correctly."""
        from clickbot.process_loader import load_process
        process = load_process("1120S")

        assert process["version"] == "2.0"
        assert "stages" in process
        assert len(process["stages"]) == 20

    def test_load_1120_with_steps(self):
        """1120.json with legacy 'steps' key still loads."""
        from clickbot.process_loader import load_process
        process = load_process("1120")

        assert "steps" in process
        assert len(process["steps"]) > 0
