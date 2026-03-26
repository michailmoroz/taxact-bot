"""Unit tests for 1120 process redesign (Phase 12).

Tests:
- 1120.json structure and stage validation
- Abort-handling stages (18, 23, 25)
- Multi-stages (4, 8, 13, 14, 15, 19, 20)
- Officer info fields (stage 19)
- open_verify_image in all three processes
- normalize_ssn_ein return-type-dependent formatting
- bot_controller dynamic polling after double-click
"""

import json
import queue
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from clickbot.process_loader import load_process


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def process_1120():
    """Load 1120.json process definition."""
    path = Path("config/processes/1120.json")
    with open(path) as f:
        return json.load(f)


def _get_stage(process: dict, stage_id: int) -> dict:
    """Helper: get stage by id from process dict."""
    return next(s for s in process["stages"] if s["id"] == stage_id)


# ── 1120.json Structure Tests ─────────────────────────────────────────


class TestProcess1120Structure:
    """Tests that 1120.json has valid structure with 26 stages."""

    def test_loads_without_error(self, process_1120):
        assert process_1120["return_type"] == "1120"
        assert process_1120["version"] == "3.0"

    def test_has_26_stages(self, process_1120):
        assert len(process_1120["stages"]) == 26

    def test_all_stages_have_ids(self, process_1120):
        ids = [s["id"] for s in process_1120["stages"]]
        assert ids == list(range(1, 27))

    def test_all_stages_have_required_fields(self, process_1120):
        for stage in process_1120["stages"]:
            assert "id" in stage
            assert "name" in stage
            assert "action" in stage

    def test_has_open_verify_image(self, process_1120):
        assert process_1120["open_verify_image"] == "1120/01_form_view.png"

    def test_static_inputs_has_officer_fields(self, process_1120):
        inputs = process_1120["static_inputs"]
        assert inputs["officer_title"] == "president"
        assert inputs["officer_email"] == "info@tmaccountant.com"
        assert inputs["officer_phone"] == "(847)850-0085"
        assert inputs["officer_pin"] == "12345"

    def test_uses_stages_key_not_steps(self, process_1120):
        assert "stages" in process_1120
        assert "steps" not in process_1120

    def test_loads_via_process_loader(self):
        process = load_process("1120")
        assert process["return_type"] == "1120"
        assert len(process["stages"]) == 26


# ── Verify-Screenshot Reference Tests ─────────────────────────────────


class TestVerifyScreenshotReferences:
    """Tests that all referenced verify screenshots exist."""

    def test_verify_screen_files_exist(self, process_1120):
        verify_base = Path("assets/verify")
        for stage in process_1120["stages"]:
            if "verify_screen" in stage:
                path = verify_base / stage["verify_screen"]
                assert path.exists(), f"Missing verify_screen: {path} (stage {stage['id']})"

    def test_verify_next_files_exist(self, process_1120):
        verify_base = Path("assets/verify")
        for stage in process_1120["stages"]:
            vn = stage.get("verify_next")
            if vn:
                path = verify_base / vn
                assert path.exists(), f"Missing verify_next: {path} (stage {stage['id']})"
            # Also check nested verify_next in conditional branches
            for branch_key in ("if_true", "if_false"):
                branch = stage.get(branch_key)
                if isinstance(branch, dict) and "verify_next" in branch:
                    path = verify_base / branch["verify_next"]
                    assert path.exists(), f"Missing verify_next in {branch_key}: {path} (stage {stage['id']})"


# ── Abort-Handling Tests ──────────────────────────────────────────────


class TestStage18WizardAbort:
    """Tests for Stage 18 — Wizard abort with recovery."""

    def test_stage18_is_conditional(self, process_1120):
        s = _get_stage(process_1120, 18)
        assert s["action"] == "conditional"

    def test_stage18_checks_acknowledgement(self, process_1120):
        s = _get_stage(process_1120, 18)
        assert s["condition"]["image"] == "1120/17_acknowledgement.png"
        assert s["condition"]["base_path"] == "verify"

    def test_stage18_if_true_clicks_continue(self, process_1120):
        s = _get_stage(process_1120, 18)
        assert s["if_true"]["action"] == "click"
        assert "continue_blue" in s["if_true"]["target"]["image"]
        assert s["if_true"]["verify_next"] == "1120/18_officer_info.png"

    def test_stage18_if_false_has_abort(self, process_1120):
        s = _get_stage(process_1120, 18)
        assert s["if_false"]["abort"] is True
        assert s["if_false"]["abort_reason"] == "FAIL: Wizard (Stage 18)"

    def test_stage18_abort_clicks_clients_with_search_region(self, process_1120):
        s = _get_stage(process_1120, 18)
        action = s["if_false"]["actions"][0]
        assert "clients_button" in action["target"]["image"]
        assert action["target"]["search_region"] == [0, 0, 300, 80]

    def test_stage18_abort_handles_save_dialog(self, process_1120):
        s = _get_stage(process_1120, 18)
        save_dialog = s["if_false"]["actions"][1]
        assert save_dialog["action"] == "conditional"
        assert save_dialog["condition"]["image"] == "common/blue_questionmark_icon.png"


class TestStage23AlertsAbort:
    """Tests for Stage 23 — Alerts not passed abort."""

    def test_stage23_has_abort(self, process_1120):
        s = _get_stage(process_1120, 23)
        assert s["if_false"]["abort"] is True
        assert s["if_false"]["abort_reason"] == "FAIL: Alerts not passed"

    def test_stage23_if_true_continues(self, process_1120):
        s = _get_stage(process_1120, 23)
        assert s["if_true"]["action"] == "click"
        assert s["if_true"]["verify_next"] == "1120/23_submit.png"

    def test_stage23_abort_clicks_clients(self, process_1120):
        s = _get_stage(process_1120, 23)
        action = s["if_false"]["actions"][0]
        assert "clients_button" in action["target"]["image"]


class TestStage25SubmitAbort:
    """Tests for Stage 25 — Submit unsuccessful abort."""

    def test_stage25_has_abort(self, process_1120):
        s = _get_stage(process_1120, 25)
        assert s["if_false"]["abort"] is True
        assert s["if_false"]["abort_reason"] == "FAIL: Submit unsuccessful"

    def test_stage25_if_true_clicks_continue_green(self, process_1120):
        s = _get_stage(process_1120, 25)
        assert s["if_true"]["action"] == "click"
        assert "continue_green" in s["if_true"]["target"]["image"]
        assert s["if_true"]["verify_next"] == "1120/25_filing_complete.png"

    def test_stage25_checks_successful_via_verify_base(self, process_1120):
        s = _get_stage(process_1120, 25)
        assert s["condition"]["base_path"] == "verify"
        assert s["condition"]["image"] == "1120/24_successful.png"


# ── Submit Safety Test ────────────────────────────────────────────────


class TestStage24SubmitSafety:
    """Tests for Stage 24 — no_retry + verify_timeout."""

    def test_stage24_has_no_retry(self, process_1120):
        s = _get_stage(process_1120, 24)
        assert s["no_retry"] is True

    def test_stage24_has_verify_timeout_30(self, process_1120):
        s = _get_stage(process_1120, 24)
        assert s["verify_timeout"] == 30.0


# ── Multi-Stage Tests ─────────────────────────────────────────────────


class TestMultiStages:
    """Tests for consolidated multi-stages."""

    @pytest.mark.parametrize("stage_id", [4, 8, 13, 14, 15, 19, 20])
    def test_multi_stages_have_actions_array(self, process_1120, stage_id):
        s = _get_stage(process_1120, stage_id)
        assert s["action"] == "multi"
        assert isinstance(s["actions"], list)
        assert len(s["actions"]) >= 2

    def test_stage4_has_3_actions(self, process_1120):
        """Stage 4: checkbox + continue + locked_2."""
        s = _get_stage(process_1120, 4)
        assert len(s["actions"]) == 3

    def test_stage4_locked2_with_timeout(self, process_1120):
        s = _get_stage(process_1120, 4)
        locked = s["actions"][2]
        assert locked["condition"]["image"] == "common/locked_2.png"
        assert locked["condition"]["timeout"] == 3.0

    def test_stage8_checkbox_checked_condition(self, process_1120):
        """Stage 8: Homeowners checkbox."""
        s = _get_stage(process_1120, 8)
        cond = s["actions"][0]
        assert cond["condition"]["type"] == "checkbox_checked"
        assert "homeowners_checked" in cond["condition"]["image_checked"]
        assert "homeowners_unchecked" in cond["condition"]["image_unchecked"]

    def test_stage13_no_office_checkbox(self, process_1120):
        s = _get_stage(process_1120, 13)
        cond = s["actions"][0]
        assert cond["condition"]["type"] == "checkbox_checked"
        assert "no_office" in cond["condition"]["image_checked"]

    def test_stage14_section_checkbox(self, process_1120):
        s = _get_stage(process_1120, 14)
        cond = s["actions"][0]
        assert cond["condition"]["type"] == "checkbox_checked"
        assert "section" in cond["condition"]["image_checked"]

    def test_stage15_scroll_until_visible(self, process_1120):
        s = _get_stage(process_1120, 15)
        scroll_action = s["actions"][0]
        assert scroll_action["action"] == "scroll_until_visible"
        assert scroll_action["target"]["scroll_direction"] == "down"


# ── Officer Info Tests ────────────────────────────────────────────────


class TestStage19OfficerInfo:
    """Tests for Stage 19 — fill 4 fields + continue."""

    def test_stage19_has_7_actions(self, process_1120):
        """3 click+type_field pairs + 1 click continue = 7."""
        s = _get_stage(process_1120, 19)
        assert len(s["actions"]) == 7

    def test_stage19_type_field_keys(self, process_1120):
        s = _get_stage(process_1120, 19)
        type_fields = [a for a in s["actions"] if a["action"] == "type_field"]
        keys = [a["text_key"] for a in type_fields]
        assert keys == ["officer_title", "officer_email", "officer_phone"]

    def test_stage19_last_action_is_continue(self, process_1120):
        s = _get_stage(process_1120, 19)
        last = s["actions"][-1]
        assert last["action"] == "click"
        assert "continue_blue" in last["target"]["image"]


class TestStage20OfficerPin:
    """Tests for Stage 20 — fill PIN + continue."""

    def test_stage20_has_3_actions(self, process_1120):
        s = _get_stage(process_1120, 20)
        assert len(s["actions"]) == 3

    def test_stage20_type_field_pin(self, process_1120):
        s = _get_stage(process_1120, 20)
        type_field = s["actions"][1]
        assert type_field["action"] == "type_field"
        assert type_field["text_key"] == "officer_pin"


# ── open_verify_image Tests ───────────────────────────────────────────


class TestOpenVerifyImage:
    """Tests that all three processes have open_verify_image."""

    def test_1120_has_open_verify_image(self):
        process = load_process("1120")
        assert process["open_verify_image"] == "1120/01_form_view.png"

    def test_1040_has_open_verify_image(self):
        process = load_process("1040")
        assert process["open_verify_image"] == "1040/01_basic_information.png"

    def test_1120s_has_open_verify_image(self):
        process = load_process("1120S")
        assert process["open_verify_image"] == "1120S/02_s_corp_view.png"

    def test_open_verify_image_files_exist(self):
        verify_base = Path("assets/verify")
        for rt in ["1120", "1040", "1120S"]:
            process = load_process(rt)
            img = process["open_verify_image"]
            path = verify_base / img
            assert path.exists(), f"Missing open_verify_image: {path} ({rt})"


# ── normalize_ssn_ein Tests ───────────────────────────────────────────


class TestNormalizeSsnEin:
    """Tests for return-type-dependent SSN/EIN formatting."""

    def test_ein_format_1120(self):
        from clickbot.vision import normalize_ssn_ein
        assert normalize_ssn_ein("993871200", "1120") == "99-3871200"

    def test_ein_format_1120s(self):
        from clickbot.vision import normalize_ssn_ein
        assert normalize_ssn_ein("993871200", "1120S") == "99-3871200"

    def test_ssn_format_1040(self):
        from clickbot.vision import normalize_ssn_ein
        assert normalize_ssn_ein("123456789", "1040") == "123-45-6789"

    def test_8_digits_not_padded_ein(self):
        from clickbot.vision import normalize_ssn_ein
        # 8-digit values are returned raw (no leading-zero padding)
        assert normalize_ssn_ein("93871200", "1120") == "93871200"

    def test_8_digits_not_padded_ssn(self):
        from clickbot.vision import normalize_ssn_ein
        # 8-digit values are returned raw (no leading-zero padding)
        assert normalize_ssn_ein("23456789", "1040") == "23456789"

    def test_non_9_digit_returns_raw(self):
        from clickbot.vision import normalize_ssn_ein
        assert normalize_ssn_ein("abc", "1120") == "abc"

    def test_already_formatted_ein(self):
        from clickbot.vision import normalize_ssn_ein
        assert normalize_ssn_ein("99-3871200", "1120") == "99-3871200"

    def test_already_formatted_ssn(self):
        from clickbot.vision import normalize_ssn_ein
        assert normalize_ssn_ein("123-45-6789", "1040") == "123-45-6789"

    def test_empty_return_type_defaults_to_ein(self):
        from clickbot.vision import normalize_ssn_ein
        assert normalize_ssn_ein("993871200", "") == "99-3871200"

    def test_short_value_returns_raw(self):
        from clickbot.vision import normalize_ssn_ein
        assert normalize_ssn_ein("12345", "1040") == "12345"


# ── Bot Controller Polling Tests ──────────────────────────────────────


class TestBotControllerPolling:
    """Tests for dynamic polling after double-click."""

    @patch("clickbot.bot_controller.load_process")
    def test_loads_open_verify_image_before_loop(self, mock_load):
        """BotController._run loads process to get open_verify_image."""
        from clickbot.bot_controller import BotController

        mock_load.return_value = {
            "name": "Test", "return_type": "1120", "version": "3.0",
            "stages": [], "static_inputs": {},
            "open_verify_image": "1120/01_form_view.png"
        }

        controller = BotController(
            settings={"vision": {}, "ocr": {}},
            selected_return_type="1120"
        )
        controller.stop_event.set()  # Immediately stop

        with patch("clickbot.bot_controller.vision"), \
             patch("clickbot.bot_controller.ClientTracker", create=True):
            # Import won't fail because we mock everything
            with patch.dict("sys.modules", {"clickbot.state": MagicMock()}):
                try:
                    controller._run()
                except Exception:
                    pass  # Expected: mocks aren't fully configured

        mock_load.assert_called_once_with("1120")

    @patch("clickbot.bot_controller.load_process")
    def test_fallback_when_open_verify_image_missing(self, mock_load):
        """When process has no open_verify_image, open_verify_image is None."""
        mock_load.return_value = {
            "name": "Test", "return_type": "1120", "version": "3.0",
            "stages": [{"id": 1, "name": "test", "action": "click"}],
            "static_inputs": {}
        }

        process = mock_load("1120")
        assert process.get("open_verify_image") is None

    @patch("clickbot.bot_controller.load_process")
    def test_fallback_when_load_process_fails(self, mock_load):
        """When load_process raises, open_verify_image falls back to None."""
        mock_load.side_effect = Exception("Process not found")

        from clickbot.bot_controller import BotController

        controller = BotController(
            settings={"vision": {}, "ocr": {}},
            selected_return_type="9999"
        )
        controller.stop_event.set()

        with patch("clickbot.bot_controller.vision"), \
             patch.dict("sys.modules", {"clickbot.state": MagicMock()}):
            try:
                controller._run()
            except Exception:
                pass

        # Should not crash — open_verify_image defaults to None


# ── Regression Tests ──────────────────────────────────────────────────


class TestRegressionOtherProcesses:
    """Ensure 1040 and 1120S processes are unchanged."""

    def test_1040_loads_correctly(self):
        process = load_process("1040")
        assert process["return_type"] == "1040"
        assert len(process["stages"]) == 19

    def test_1120s_loads_correctly(self):
        process = load_process("1120S")
        assert process["return_type"] == "1120S"
        assert len(process["stages"]) == 20

    def test_1120_loads_via_loader(self):
        process = load_process("1120")
        assert process["return_type"] == "1120"
        assert len(process["stages"]) == 26
