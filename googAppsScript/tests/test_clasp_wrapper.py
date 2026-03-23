"""Tests for gas_skill.clasp_wrapper."""
import json
from unittest.mock import patch, MagicMock

from gas_skill.clasp_wrapper import ClaspWrapper
from gas_skill.models import CommandResult


def _ok(stdout="", cmd="clasp"):
    return CommandResult(command=cmd, exit_code=0, stdout=stdout, stderr="",
                         success=True, duration_sec=0.1)


def _fail(stderr="error", cmd="clasp"):
    return CommandResult(command=cmd, exit_code=1, stdout="", stderr=stderr,
                         success=False, duration_sec=0.1)


class TestClaspWrapper:
    @patch("gas_skill.clasp_wrapper.run_command")
    def test_push(self, mock_run, mock_config):
        mock_run.return_value = _ok("Pushed 4 files.")
        cw = ClaspWrapper(mock_config)
        result = cw.push()
        assert result.success is True
        mock_run.assert_called_once_with(["clasp", "push"], cwd=mock_config.project_root)

    @patch("gas_skill.clasp_wrapper.run_command")
    def test_pull(self, mock_run, mock_config):
        mock_run.return_value = _ok("Pulled 3 files.")
        cw = ClaspWrapper(mock_config)
        result = cw.pull()
        assert result.success is True

    @patch("gas_skill.clasp_wrapper.run_command")
    def test_run_without_params(self, mock_run, mock_config):
        mock_run.return_value = _ok('{"result": "ok"}')
        cw = ClaspWrapper(mock_config)
        result = cw.run("myFunction")
        assert result.success is True
        mock_run.assert_called_once_with(
            ["clasp", "run", "myFunction"],
            cwd=mock_config.project_root, timeout=360,
        )

    @patch("gas_skill.clasp_wrapper.run_command")
    def test_run_with_params(self, mock_run, mock_config):
        mock_run.return_value = _ok()
        cw = ClaspWrapper(mock_config)
        cw.run("fn", params='["arg1"]')
        mock_run.assert_called_once_with(
            ["clasp", "run", "fn", "--params", '["arg1"]'],
            cwd=mock_config.project_root, timeout=360,
        )

    @patch("gas_skill.clasp_wrapper.run_command")
    def test_logs_json(self, mock_run, mock_config):
        mock_run.return_value = _ok("[]")
        cw = ClaspWrapper(mock_config)
        cw.logs(json_output=True)
        mock_run.assert_called_once_with(
            ["clasp", "logs", "--json"], cwd=mock_config.project_root,
        )

    @patch("gas_skill.clasp_wrapper.run_command")
    def test_logs_no_json(self, mock_run, mock_config):
        mock_run.return_value = _ok()
        cw = ClaspWrapper(mock_config)
        cw.logs(json_output=False)
        mock_run.assert_called_once_with(
            ["clasp", "logs"], cwd=mock_config.project_root,
        )

    @patch("gas_skill.clasp_wrapper.run_command")
    def test_create(self, mock_run, mock_config):
        mock_run.return_value = _ok()
        cw = ClaspWrapper(mock_config)
        cw.create("sheets", "My Project")
        mock_run.assert_called_once_with(
            ["clasp", "create", "--type", "sheets", "--title", "My Project"],
            cwd=mock_config.project_root,
        )

    @patch("gas_skill.clasp_wrapper.run_command")
    def test_deploy(self, mock_run, mock_config):
        mock_run.return_value = _ok()
        cw = ClaspWrapper(mock_config)
        cw.deploy(description="v1.0")
        mock_run.assert_called_once_with(
            ["clasp", "deploy", "-d", "v1.0"], cwd=mock_config.project_root,
        )

    def test_get_script_id(self, mock_config, mock_clasp_json):
        cw = ClaspWrapper(mock_config)
        sid = cw.get_script_id()
        assert sid == "test-script-id-12345"

    def test_get_script_id_missing(self, mock_config):
        cw = ClaspWrapper(mock_config)
        assert cw.get_script_id() is None
