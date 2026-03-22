"""Unit tests for 1040 process JSON and Phase 10b-1 fixes."""

import json
import queue
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from clickbot.process_executor import ProcessExecutor, ExecutionResult


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def process_1040():
    """Load 1040.json process definition."""
    path = Path("config/processes/1040.json")
    with open(path) as f:
        return json.load(f)


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
            "max_retries": 1,
            "min_wait_after_ms": 10,
            "verify_base_path": "assets/verify",
        },
        "ocr": {},
    }
    msg_queue = queue.Queue()
    stop_event = threading.Event()
    return ProcessExecutor(settings, msg_queue, stop_event)


def _get_stage(process: dict, stage_id: int) -> dict:
    """Helper: get stage by id from process dict."""
    return next(s for s in process["stages"] if s["id"] == stage_id)


# ── 1040.json Structure Tests ─────────────────────────────────────────


class TestProcess1040Loads:
    """Tests that 1040.json loads and has valid structure."""

    def test_loads_without_error(self, process_1040):
        assert process_1040["return_type"] == "1040"
        assert len(process_1040["stages"]) == 19

    def test_all_stages_have_ids(self, process_1040):
        ids = [s["id"] for s in process_1040["stages"]]
        assert ids == list(range(1, 20))


class TestStage3LockedHandling:
    """Tests for Stage 3 — locked checkbox + locked_2."""

    def test_stage3_is_multi_with_3_actions(self, process_1040):
        s3 = _get_stage(process_1040, 3)
        assert s3["action"] == "multi"
        assert len(s3["actions"]) == 3

    def test_stage3_sub1_conditional_checkbox(self, process_1040):
        s3 = _get_stage(process_1040, 3)
        sub1 = s3["actions"][0]
        assert sub1["action"] == "conditional"
        assert sub1["condition"]["type"] == "element_visible"
        assert "unchecked" in sub1["condition"]["image"]

    def test_stage3_sub2_click_continue(self, process_1040):
        s3 = _get_stage(process_1040, 3)
        sub2 = s3["actions"][1]
        assert sub2["action"] == "click"
        assert "continue_blue" in sub2["target"]["image"]

    def test_stage3_sub3_locked2_with_timeout(self, process_1040):
        s3 = _get_stage(process_1040, 3)
        sub3 = s3["actions"][2]
        assert sub3["action"] == "conditional"
        assert sub3["condition"]["type"] == "element_visible"
        assert "locked_2" in sub3["condition"]["image"]
        assert sub3["condition"]["timeout"] == 3.0

    def test_stage3_sub3_unlocks_on_true(self, process_1040):
        s3 = _get_stage(process_1040, 3)
        sub3 = s3["actions"][2]
        assert sub3["if_true"]["action"] == "click"
        assert "unlock_and_save" in sub3["if_true"]["target"]["image"]

    def test_stage3_has_verify_next(self, process_1040):
        s3 = _get_stage(process_1040, 3)
        assert s3["verify_next"] == "1040/04_federal_extension.png"


class TestStage12AbortReason:
    """Tests for Stage 12 — wizard abort."""

    def test_stage12_has_abort_reason(self, process_1040):
        s12 = _get_stage(process_1040, 12)
        assert s12["if_false"]["abort"] is True
        assert s12["if_false"]["abort_reason"] == "FAIL: Wizard (Stage 12)"

    def test_stage12_clients_button_has_search_region(self, process_1040):
        s12 = _get_stage(process_1040, 12)
        clients_action = s12["if_false"]["actions"][0]
        assert clients_action["target"]["search_region"] == [0, 0, 300, 80]

    def test_stage12_no_default_has_search_region(self, process_1040):
        s12 = _get_stage(process_1040, 12)
        no_default_cond = s12["if_false"]["actions"][1]
        assert no_default_cond["if_true"]["target"]["search_region"] == [560, 340, 800, 400]


class TestStage16CleanAbort:
    """Tests for Stage 16 — alerts not passed (nested conditional)."""

    def test_stage16_if_false_is_conditional(self, process_1040):
        s16 = _get_stage(process_1040, 16)
        assert s16["if_false"]["action"] == "conditional"
        assert s16["if_false"]["condition"]["image"] == "1040/missing_address.png"

    def test_stage16_missing_address_abort(self, process_1040):
        s16 = _get_stage(process_1040, 16)
        branch = s16["if_false"]["if_true"]
        assert branch["abort"] is True
        assert branch["abort_reason"] == "FAIL: missing address"
        assert "clients_button" in branch["actions"][0]["target"]["image"]

    def test_stage16_generic_alerts_abort(self, process_1040):
        s16 = _get_stage(process_1040, 16)
        branch = s16["if_false"]["if_false"]
        assert branch["abort"] is True
        assert branch["abort_reason"] == "FAIL: Alerts not passed"
        assert "clients_button" in branch["actions"][0]["target"]["image"]


class TestStage18CleanAbort:
    """Tests for Stage 18 — submit unsuccessful."""

    def test_stage18_has_abort(self, process_1040):
        s18 = _get_stage(process_1040, 18)
        assert s18["if_false"]["abort"] is True
        assert s18["if_false"]["abort_reason"] == "FAIL: Submit unsuccessful"

    def test_stage18_clicks_clients_button(self, process_1040):
        s18 = _get_stage(process_1040, 18)
        actions = s18["if_false"]["actions"]
        assert len(actions) == 1
        assert "clients_button" in actions[0]["target"]["image"]


# ── ExecutionResult Tests ─────────────────────────────────────────────


class TestExecutionResultAbortReason:
    """Tests for abort_reason field in ExecutionResult."""

    def test_abort_reason_defaults_to_none(self):
        r = ExecutionResult(True, 1, 1)
        assert r.abort_reason is None

    def test_abort_reason_set_explicitly(self):
        r = ExecutionResult(False, 0, 1, abort_reason="FAIL: test")
        assert r.abort_reason == "FAIL: test"

    def test_abort_reason_with_error_message(self):
        r = ExecutionResult(
            False, 5, 19,
            error_message="Step failed: handle_post_efile",
            error_step=12,
            abort_reason="FAIL: Wizard (Stage 12)"
        )
        assert r.error_message == "Step failed: handle_post_efile"
        assert r.abort_reason == "FAIL: Wizard (Stage 12)"


# ── ProcessExecutor abort_reason Propagation ──────────────────────────


class TestAbortReasonPropagation:
    """Tests that abort_reason flows from JSON branch to ExecutionResult."""

    def test_execute_branch_stores_abort_reason(self, executor):
        """_execute_branch with abort dict stores abort_reason."""
        branch = {
            "abort": True,
            "abort_reason": "FAIL: test reason",
            "actions": []
        }
        result = executor._execute_branch(branch, {})
        assert result is False
        assert executor._last_abort_reason == "FAIL: test reason"

    def test_execute_branch_abort_without_reason(self, executor):
        """_execute_branch with abort but no reason stores None."""
        branch = {
            "abort": True,
            "actions": []
        }
        result = executor._execute_branch(branch, {})
        assert result is False
        assert executor._last_abort_reason is None

    def test_abort_reason_reset_on_new_execute(self, executor):
        """abort_reason is reset at start of each execute() call."""
        executor._last_abort_reason = "leftover"

        with patch("clickbot.process_executor.load_process") as mock_load:
            mock_load.return_value = {
                "name": "Test", "return_type": "1040", "version": "1.0",
                "stages": [], "static_inputs": {}
            }
            executor.execute("1040")

        assert executor._last_abort_reason is None


# ── search_region Tests ───────────────────────────────────────────────


class TestSearchRegion:
    """Tests for search_region support in click actions."""

    @patch("clickbot.process_executor.vision.find_element")
    @patch("clickbot.process_executor.executor.click")
    def test_action_click_passes_search_region(self, mock_click, mock_find, executor):
        """_action_click passes search_region to vision.find_element."""
        mock_find.return_value = (100, 200)
        mock_click.return_value = True

        target = {
            "image": "test.png",
            "search_region": [0, 0, 300, 80]
        }
        executor._action_click(target)

        mock_find.assert_called_once_with(
            "test.png", None, None, region=(0, 0, 300, 80)
        )

    @patch("clickbot.process_executor.vision.find_element")
    @patch("clickbot.process_executor.executor.click")
    def test_action_click_no_search_region(self, mock_click, mock_find, executor):
        """_action_click without search_region passes None."""
        mock_find.return_value = (100, 200)
        mock_click.return_value = True

        target = {"image": "test.png"}
        executor._action_click(target)

        mock_find.assert_called_once_with("test.png", None, None, region=None)

    @patch("clickbot.process_executor.vision.find_element")
    @patch("clickbot.process_executor.executor.double_click")
    def test_action_double_click_passes_search_region(self, mock_dbl, mock_find, executor):
        """_action_double_click passes search_region to vision.find_element."""
        mock_find.return_value = (100, 200)
        mock_dbl.return_value = True

        target = {
            "image": "test.png",
            "search_region": [500, 300, 200, 100]
        }
        executor._action_double_click(target)

        mock_find.assert_called_once_with(
            "test.png", None, None, region=(500, 300, 200, 100)
        )


# ── Timeout Condition Tests ───────────────────────────────────────────


class TestTimeoutCondition:
    """Tests for timeout in element_visible condition."""

    @patch("clickbot.process_executor.vision.wait_for_element")
    def test_condition_with_timeout_uses_wait_for_element(self, mock_wait, executor):
        """element_visible with timeout uses wait_for_element."""
        mock_wait.return_value = (100, 200)

        step = {
            "action": "conditional",
            "condition": {
                "type": "element_visible",
                "image": "common/locked_2.png",
                "timeout": 5.0
            },
            "if_true": "continue",
            "if_false": "continue"
        }
        result = executor._action_conditional(step, {})

        assert result is True
        mock_wait.assert_called_once()
        call_kwargs = mock_wait.call_args
        assert call_kwargs[1]["timeout"] == 5.0
        assert call_kwargs[1]["stop_event"] is executor.stop_event

    @patch("clickbot.process_executor.vision.find_element")
    def test_condition_without_timeout_uses_find_element(self, mock_find, executor):
        """element_visible without timeout uses find_element."""
        mock_find.return_value = (100, 200)

        step = {
            "action": "conditional",
            "condition": {
                "type": "element_visible",
                "image": "common/test.png"
            },
            "if_true": "continue",
            "if_false": "continue"
        }
        result = executor._action_conditional(step, {})

        assert result is True
        mock_find.assert_called_once()

    @patch("clickbot.process_executor.vision.wait_for_element")
    def test_condition_timeout_not_found_goes_if_false(self, mock_wait, executor):
        """element_visible with timeout returns None -> if_false branch."""
        mock_wait.return_value = None

        step = {
            "action": "conditional",
            "condition": {
                "type": "element_visible",
                "image": "common/locked_2.png",
                "timeout": 2.0
            },
            "if_true": "continue",
            "if_false": "continue"
        }
        result = executor._action_conditional(step, {})
        assert result is True  # "continue" branch returns True


# ── 1120S Regression Test ─────────────────────────────────────────────


class TestRegressionOtherProcesses:
    """Ensure 1120S and 1120 processes are unchanged."""

    def test_1120s_loads_correctly(self):
        from clickbot.process_loader import load_process
        process = load_process("1120S")
        assert process["return_type"] == "1120S"
        assert len(process["stages"]) == 20

    def test_1120_loads_correctly(self):
        from clickbot.process_loader import load_process
        process = load_process("1120")
        assert process["return_type"] == "1120"
        assert "steps" in process
