"""Tests for gas_skill._subprocess."""
from gas_skill._subprocess import run_command


class TestRunCommand:
    def test_successful_command(self):
        result = run_command(["echo", "hello"])
        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout == "hello"
        assert result.stderr == ""
        assert result.duration_sec >= 0

    def test_failing_command(self):
        result = run_command(["false"])
        assert result.success is False
        assert result.exit_code != 0

    def test_command_not_found(self):
        result = run_command(["nonexistent_command_xyz_123"])
        assert result.success is False
        assert result.exit_code == -1
        assert "Command not found" in result.stderr

    def test_timeout(self):
        result = run_command(["sleep", "10"], timeout=1)
        assert result.success is False
        assert result.exit_code == -1
        assert "timed out" in result.stderr

    def test_cwd(self, tmp_path):
        result = run_command(["pwd"], cwd=tmp_path)
        assert result.success is True
        assert str(tmp_path) in result.stdout

    def test_command_string(self):
        result = run_command(["echo", "a", "b"])
        assert result.command == "echo a b"
