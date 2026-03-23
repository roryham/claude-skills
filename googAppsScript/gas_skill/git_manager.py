"""git_manager.py — Git and GitHub CLI operations with branch safety."""
import shutil
from pathlib import Path
from ._subprocess import run_command
from .models import CommandResult
from .config import ProjectConfig
from .exceptions import BranchProtectionError, DirtyTreeError, ConfigError


class GitManager:
    """Manages Git operations with branch strategy enforcement."""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.project_root = config.project_root

    # ── Query methods ──────────────────────────────────────────

    def current_branch(self) -> str:
        result = self._git(["branch", "--show-current"])
        return result.stdout.strip()

    def head_hash(self, short: bool = True) -> str:
        args = ["rev-parse"]
        if short:
            args.append("--short")
        args.append("HEAD")
        result = self._git(args)
        return result.stdout.strip()

    def is_clean(self) -> bool:
        result = self._git(["status", "--porcelain"])
        return result.stdout.strip() == ""

    def list_branches(self, remote: bool = False) -> list[str]:
        args = ["branch"]
        if remote:
            args.append("-a")
        result = self._git(args)
        return [
            line.strip().lstrip("* ")
            for line in result.stdout.splitlines()
            if line.strip()
        ]

    def latest_tag(self) -> str | None:
        result = self._git(["describe", "--tags", "--abbrev=0"])
        if result.success:
            return result.stdout.strip()
        return None

    def remote_sync_status(self) -> dict:
        self._git(["fetch", "origin"])
        branch = self.current_branch()
        ahead = self._git(
            ["rev-list", "--count", f"origin/{branch}..{branch}"]
        )
        behind = self._git(
            ["rev-list", "--count", f"{branch}..origin/{branch}"]
        )
        return {
            "ahead": int(ahead.stdout.strip()) if ahead.success else 0,
            "behind": int(behind.stdout.strip()) if behind.success else 0,
        }

    # ── Safety checks ─────────────────────────────────────────

    def _require_clean_tree(self) -> None:
        if not self.is_clean():
            raise DirtyTreeError("Working tree has uncommitted changes")

    def _require_not_main(self) -> None:
        if self.current_branch() == self.config.main_branch:
            raise BranchProtectionError(
                f"Direct commits to '{self.config.main_branch}' are not allowed"
            )

    def _require_branch_exists(self, branch: str) -> None:
        result = self._git(["rev-parse", "--verify", branch])
        if not result.success:
            raise ConfigError(f"Branch '{branch}' does not exist")

    # ── Mutation methods ───────────────────────────────────────

    def checkout(self, branch: str) -> CommandResult:
        self._require_clean_tree()
        result = self._git(["checkout", branch])
        if result.success:
            self._swap_clasp_config(branch)
        return result

    def create_branch(self, name: str, from_branch: str | None = None) -> CommandResult:
        self._require_clean_tree()
        if from_branch:
            self.checkout(from_branch)
            self._git(["pull", "origin", from_branch])
        result = self._git(["checkout", "-b", name])
        if result.success:
            self._swap_clasp_config(name)
            self._git(["push", "-u", "origin", name])
        return result

    def add_all(self) -> CommandResult:
        return self._git(["add", "-A"])

    def commit(self, message: str) -> CommandResult:
        self._require_not_main()
        return self._git(["commit", "-m", message])

    def push(self, branch: str | None = None) -> CommandResult:
        branch = branch or self.current_branch()
        return self._git(["push", "origin", branch])

    def pull(self, branch: str | None = None) -> CommandResult:
        branch = branch or self.current_branch()
        return self._git(["pull", "origin", branch])

    def merge(self, source: str, target: str, message: str) -> CommandResult:
        self.checkout(target)
        self.pull(target)
        return self._git(["merge", "--no-ff", source, "-m", message])

    def tag(self, version: str, message: str) -> CommandResult:
        return self._git(["tag", "-a", version, "-m", message])

    def push_tag(self, version: str) -> CommandResult:
        return self._git(["push", "origin", version])

    def delete_branch(self, branch: str, remote: bool = True) -> CommandResult:
        result = self._git(["branch", "-d", branch])
        if result.success and remote:
            self._git(["push", "origin", "--delete", branch])
        return result

    def abort_merge(self) -> CommandResult:
        return self._git(["merge", "--abort"])

    def reset_hard(self, ref: str = "HEAD") -> CommandResult:
        return self._git(["reset", "--hard", ref])

    # ── GitHub CLI methods ─────────────────────────────────────

    def gh_auth_status(self) -> CommandResult:
        return run_command(["gh", "auth", "status"], cwd=self.project_root)

    def gh_create_release(
        self, version: str, title: str, notes_file: str
    ) -> CommandResult:
        return run_command(
            [
                "gh", "release", "create", version,
                "--title", title,
                "--notes-file", notes_file,
            ],
            cwd=self.project_root,
        )

    # ── Internal helpers ───────────────────────────────────────

    def _git(self, args: list[str]) -> CommandResult:
        return run_command(["git"] + args, cwd=self.project_root)

    def _swap_clasp_config(self, branch: str) -> None:
        if branch == self.config.main_branch:
            source = self.project_root / self.config.prod_config
        else:
            source = self.project_root / self.config.dev_config

        target = self.project_root / ".clasp.json"

        if source.exists():
            shutil.copy2(source, target)
