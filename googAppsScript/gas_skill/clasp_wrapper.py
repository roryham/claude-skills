"""clasp_wrapper.py — Wrapper for all clasp CLI operations."""
from pathlib import Path
from ._subprocess import run_command
from .models import CommandResult
from .config import ProjectConfig


class ClaspWrapper:
    """Manages all interactions with the clasp CLI."""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.project_root = config.project_root

    def push(self) -> CommandResult:
        """Push local files to the remote Apps Script project."""
        return run_command(["clasp", "push"], cwd=self.project_root)

    def pull(self) -> CommandResult:
        """Pull remote files to the local project."""
        return run_command(["clasp", "pull"], cwd=self.project_root)

    def run(self, function_name: str, params: str | None = None) -> CommandResult:
        """Execute a function in the remote Apps Script project."""
        args = ["clasp", "run", function_name]
        if params:
            args.extend(["--params", params])
        return run_command(args, cwd=self.project_root, timeout=360)

    def logs(self, json_output: bool = True) -> CommandResult:
        """Retrieve execution logs."""
        args = ["clasp", "logs"]
        if json_output:
            args.append("--json")
        return run_command(args, cwd=self.project_root)

    def create(self, project_type: str, title: str) -> CommandResult:
        """Create a new Apps Script project."""
        return run_command(
            ["clasp", "create", "--type", project_type, "--title", title],
            cwd=self.project_root,
        )

    def clone(self, script_id: str) -> CommandResult:
        """Clone an existing Apps Script project."""
        return run_command(
            ["clasp", "clone", script_id],
            cwd=self.project_root,
        )

    def deploy(self, description: str = "") -> CommandResult:
        """Create a versioned deployment."""
        args = ["clasp", "deploy"]
        if description:
            args.extend(["-d", description])
        return run_command(args, cwd=self.project_root)

    def status(self) -> CommandResult:
        """Check clasp project status."""
        return run_command(["clasp", "status"], cwd=self.project_root)

    def get_script_id(self) -> str | None:
        """Read scriptId from the active .clasp.json."""
        import json
        clasp_json = self.project_root / ".clasp.json"
        if not clasp_json.exists():
            return None
        with open(clasp_json) as f:
            data = json.load(f)
        return data.get("scriptId")
