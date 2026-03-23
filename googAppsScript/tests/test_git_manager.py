"""Tests for gas_skill.git_manager."""
import json
from unittest.mock import patch, call

import pytest

from gas_skill.git_manager import GitManager
from gas_skill.models import CommandResult
from gas_skill.exceptions import BranchProtectionError, DirtyTreeError, ConfigError


def _ok(stdout="", cmd="git"):
    return CommandResult(command=cmd, exit_code=0, stdout=stdout, stderr="",
                         success=True, duration_sec=0.1)


def _fail(stderr="error", cmd="git"):
    return CommandResult(command=cmd, exit_code=1, stdout="", stderr=stderr,
                         success=False, duration_sec=0.1)


class TestGitManagerQuery:
    @patch("gas_skill.git_manager.run_command")
    def test_current_branch(self, mock_run, mock_config):
        mock_run.return_value = _ok("feature/test")
        gm = GitManager(mock_config)
        assert gm.current_branch() == "feature/test"

    @patch("gas_skill.git_manager.run_command")
    def test_head_hash(self, mock_run, mock_config):
        mock_run.return_value = _ok("abc1234")
        gm = GitManager(mock_config)
        assert gm.head_hash() == "abc1234"

    @patch("gas_skill.git_manager.run_command")
    def test_is_clean_true(self, mock_run, mock_config):
        mock_run.return_value = _ok("")
        gm = GitManager(mock_config)
        assert gm.is_clean() is True

    @patch("gas_skill.git_manager.run_command")
    def test_is_clean_false(self, mock_run, mock_config):
        mock_run.return_value = _ok("M file.py")
        gm = GitManager(mock_config)
        assert gm.is_clean() is False

    @patch("gas_skill.git_manager.run_command")
    def test_list_branches(self, mock_run, mock_config):
        mock_run.return_value = _ok("  main\n* develop\n  feature/x")
        gm = GitManager(mock_config)
        branches = gm.list_branches()
        assert "main" in branches
        assert "develop" in branches
        assert "feature/x" in branches

    @patch("gas_skill.git_manager.run_command")
    def test_latest_tag_exists(self, mock_run, mock_config):
        mock_run.return_value = _ok("v1.2.3")
        gm = GitManager(mock_config)
        assert gm.latest_tag() == "v1.2.3"

    @patch("gas_skill.git_manager.run_command")
    def test_latest_tag_none(self, mock_run, mock_config):
        mock_run.return_value = _fail("no tags")
        gm = GitManager(mock_config)
        assert gm.latest_tag() is None


class TestGitManagerSafety:
    @patch("gas_skill.git_manager.run_command")
    def test_require_clean_tree_raises(self, mock_run, mock_config):
        mock_run.return_value = _ok("M dirty.py")
        gm = GitManager(mock_config)
        with pytest.raises(DirtyTreeError):
            gm._require_clean_tree()

    @patch("gas_skill.git_manager.run_command")
    def test_require_not_main_raises(self, mock_run, mock_config):
        mock_run.return_value = _ok("main")
        gm = GitManager(mock_config)
        with pytest.raises(BranchProtectionError):
            gm._require_not_main()

    @patch("gas_skill.git_manager.run_command")
    def test_require_not_main_ok(self, mock_run, mock_config):
        mock_run.return_value = _ok("develop")
        gm = GitManager(mock_config)
        gm._require_not_main()  # Should not raise

    @patch("gas_skill.git_manager.run_command")
    def test_commit_on_main_blocked(self, mock_run, mock_config):
        mock_run.return_value = _ok("main")
        gm = GitManager(mock_config)
        with pytest.raises(BranchProtectionError):
            gm.commit("bad commit")


class TestGitManagerMutation:
    @patch("gas_skill.git_manager.run_command")
    def test_add_all(self, mock_run, mock_config):
        mock_run.return_value = _ok()
        gm = GitManager(mock_config)
        result = gm.add_all()
        assert result.success is True

    @patch("gas_skill.git_manager.run_command")
    def test_push(self, mock_run, mock_config):
        # First call: current_branch, second call: push
        mock_run.side_effect = [_ok("develop"), _ok()]
        gm = GitManager(mock_config)
        result = gm.push()
        assert result.success is True

    @patch("gas_skill.git_manager.run_command")
    def test_tag(self, mock_run, mock_config):
        mock_run.return_value = _ok()
        gm = GitManager(mock_config)
        result = gm.tag("v1.0.0", "Release 1.0")
        assert result.success is True


class TestClaspConfigSwap:
    @patch("gas_skill.git_manager.run_command")
    def test_swap_to_dev(self, mock_run, mock_config, mock_clasp_dev_json):
        gm = GitManager(mock_config)
        gm._swap_clasp_config("develop")
        clasp_json = mock_config.project_root / ".clasp.json"
        assert clasp_json.exists()
        data = json.loads(clasp_json.read_text())
        assert data["scriptId"] == "test-script-id-12345"

    @patch("gas_skill.git_manager.run_command")
    def test_swap_to_prod(self, mock_run, mock_config, mock_clasp_prod_json):
        gm = GitManager(mock_config)
        gm._swap_clasp_config("main")
        clasp_json = mock_config.project_root / ".clasp.json"
        assert clasp_json.exists()
        data = json.loads(clasp_json.read_text())
        assert data["scriptId"] == "prod-script-id-99999"

    @patch("gas_skill.git_manager.run_command")
    def test_swap_missing_config_no_error(self, mock_run, mock_config):
        """When config file doesn't exist, _swap_clasp_config silently skips."""
        gm = GitManager(mock_config)
        # Should not raise since we made it tolerant
        gm._swap_clasp_config("develop")
