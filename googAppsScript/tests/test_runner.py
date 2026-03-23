"""Tests for gas_skill.runner."""
import json
from unittest.mock import patch, MagicMock

from gas_skill.runner import FeedbackLoopRunner
from gas_skill.models import CommandResult, ErrorCategory


def _ok(stdout="", cmd="cmd"):
    return CommandResult(command=cmd, exit_code=0, stdout=stdout, stderr="",
                         success=True, duration_sec=0.1)


def _fail(stderr="error", cmd="cmd"):
    return CommandResult(command=cmd, exit_code=1, stdout="", stderr=stderr,
                         success=False, duration_sec=0.1)


class TestFeedbackLoopRunner:
    def _make_runner(self, mock_config, git, clasp):
        """Create a runner with mocked git/clasp and bypassed validation."""
        runner = FeedbackLoopRunner(mock_config)
        runner.git = git
        runner.clasp = clasp
        return runner

    @patch("gas_skill.runner.time.sleep")
    def test_successful_run(self, mock_sleep, mock_config, valid_manifest,
                             mock_clasp_json, mock_clasp_dev_json):
        git = MagicMock()
        git.is_clean.return_value = True
        git.current_branch.return_value = "feature/test"
        git.head_hash.return_value = "abc1234"
        git.push.return_value = _ok()

        clasp = MagicMock()
        clasp.push.return_value = _ok("Pushed 4 files.")

        test_output = json.dumps({
            "total": 2, "passed": 2, "failed": 0, "errors": 0,
            "success": True, "details": [],
        })
        clasp.run.return_value = _ok(f"> runAllTests\n{test_output}")

        runner = self._make_runner(mock_config, git, clasp)
        report = runner.run()
        assert report.success is True
        assert report.total_iterations == 1

    @patch("gas_skill.runner.time.sleep")
    def test_push_failure(self, mock_sleep, mock_config, valid_manifest,
                           mock_clasp_json, mock_clasp_dev_json):
        git = MagicMock()
        git.is_clean.return_value = True
        git.current_branch.return_value = "feature/test"
        git.head_hash.return_value = "abc1234"

        clasp = MagicMock()
        clasp.push.return_value = _fail("SyntaxError: Unexpected token")

        runner = self._make_runner(mock_config, git, clasp)
        report = runner.run()
        assert report.success is False
        assert report.action_needed == "FIX_PUSH_ERROR"
        assert report.iterations[0].error_category == ErrorCategory.SYNTAX

    @patch("gas_skill.runner.time.sleep")
    def test_test_failure(self, mock_sleep, mock_config, valid_manifest,
                           mock_clasp_json, mock_clasp_dev_json):
        git = MagicMock()
        git.is_clean.return_value = True
        git.current_branch.return_value = "feature/test"
        git.head_hash.return_value = "abc1234"

        clasp = MagicMock()
        clasp.push.return_value = _ok("Pushed 4 files.")

        test_output = json.dumps({
            "total": 2, "passed": 1, "failed": 1, "errors": 0,
            "success": False,
            "details": [
                {"function": "t1", "status": "PASS", "message": "ok",
                 "timestamp": "", "stack": ""},
                {"function": "t2", "status": "FAIL",
                 "message": "Expected 1 got 2", "timestamp": "", "stack": ""},
            ],
        })
        clasp.run.return_value = _ok(f"> runAllTests\n{test_output}")

        runner = self._make_runner(mock_config, git, clasp)
        report = runner.run()
        assert report.success is False
        assert report.action_needed == "FIX_TEST_FAILURE"

    @patch("gas_skill.runner.time.sleep")
    def test_auto_commit_dirty_tree(self, mock_sleep, mock_config, valid_manifest,
                                     mock_clasp_json, mock_clasp_dev_json):
        git = MagicMock()
        git.is_clean.side_effect = [False, True, True]
        git.current_branch.return_value = "feature/test"
        git.head_hash.return_value = "def5678"
        git.add_all.return_value = _ok()
        git._git.return_value = _ok()
        git.push.return_value = _ok()

        clasp = MagicMock()
        clasp.push.return_value = _ok("Pushed 4 files.")

        test_output = json.dumps({
            "total": 1, "passed": 1, "failed": 0, "errors": 0,
            "success": True, "details": [],
        })
        clasp.run.return_value = _ok(f"> runAllTests\n{test_output}")

        runner = self._make_runner(mock_config, git, clasp)
        report = runner.run()
        assert report.success is True
        git.add_all.assert_called()

    @patch("gas_skill.runner.time.sleep")
    def test_runtime_error(self, mock_sleep, mock_config, valid_manifest,
                            mock_clasp_json, mock_clasp_dev_json):
        git = MagicMock()
        git.is_clean.return_value = True
        git.current_branch.return_value = "feature/test"
        git.head_hash.return_value = "abc1234"

        clasp = MagicMock()
        clasp.push.return_value = _ok("Pushed 4 files.")
        clasp.run.return_value = _fail("ReferenceError: myFunc is not defined")

        runner = self._make_runner(mock_config, git, clasp)
        report = runner.run()
        assert report.success is False
        assert report.action_needed == "FIX_RUNTIME_ERROR"


class TestValidatePrePush:
    def test_validate_checks(self, mock_config, mock_clasp_json, mock_clasp_dev_json,
                              valid_manifest):
        git = MagicMock()
        git.current_branch.return_value = "feature/test"
        git.is_clean.return_value = True

        runner = FeedbackLoopRunner(mock_config)
        runner.git = git

        checks = runner._validate_pre_push()
        check_names = [c["check"] for c in checks]
        assert "not_on_main" in check_names
        assert "clasp_config_exists" in check_names
        assert "clean_working_tree" in check_names
        assert "valid_manifest" in check_names
        assert all(c["passed"] for c in checks if c["check"] != "manifest_warning")

    def test_on_main_fails(self, mock_config, mock_clasp_json, valid_manifest):
        git = MagicMock()
        git.current_branch.return_value = "main"
        git.is_clean.return_value = True

        runner = FeedbackLoopRunner(mock_config)
        runner.git = git

        checks = runner._validate_pre_push()
        main_check = next(c for c in checks if c["check"] == "not_on_main")
        assert main_check["passed"] is False
