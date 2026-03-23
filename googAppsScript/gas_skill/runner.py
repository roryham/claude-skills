"""runner.py — Feedback loop engine for push-run-fix cycles."""
from __future__ import annotations

import json
import time
from pathlib import Path

from .config import ProjectConfig
from .git_manager import GitManager
from .clasp_wrapper import ClaspWrapper
from .log_parser import classify_error, parse_test_output
from .manifest import validate as validate_manifest
from .models import (
    CommandResult,
    ErrorCategory,
    IterationRecord,
    LoopReport,
    TestReport,
)
from .exceptions import PrePushValidationError


class FeedbackLoopRunner:
    """
    Orchestrates the push -> run -> evaluate -> report cycle.

    Design principle: the runner does NOT attempt to fix code.
    It pushes, runs tests, and returns structured results.
    Claude Code is the intelligent agent that reads the results,
    decides on a fix, edits files, and invokes the runner again.
    """

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.git = GitManager(config)
        self.clasp = ClaspWrapper(config)
        self.project_root = config.project_root

    def run(
        self,
        max_retries: int | None = None,
        delay: int | None = None,
    ) -> LoopReport:
        """
        Execute one iteration of the feedback loop.

        Despite the name 'run' and the max_retries parameter,
        this method performs a SINGLE push-run-evaluate cycle
        and returns the result. The max_retries parameter is
        tracked for reporting purposes so Claude Code knows
        how many attempts remain.

        Returns:
            LoopReport with success status and detailed results.
        """
        max_retries = max_retries or self.config.max_retries
        delay = delay or self.config.retry_delay_sec
        log_wait = self.config.log_wait_sec

        iterations: list[IterationRecord] = []
        record = IterationRecord(iteration=1)

        # ── Step 1: Auto-commit if dirty ─────────────────────
        if not self.git.is_clean():
            self.git.add_all()
            commit_result = self.git._git(
                ["commit", "-m", "fix(auto): pre-push auto-commit"]
            )
            if commit_result.success:
                record.committed = True
                record.commit_hash = self.git.head_hash()

        # ── Step 2: Pre-push validation ──────────────────────
        try:
            checks = self._validate_pre_push()
            failed_checks = [c for c in checks if not c["passed"]]
            if failed_checks:
                record.error_category = ErrorCategory.MANIFEST
                iterations.append(record)
                return LoopReport(
                    success=False,
                    total_iterations=1,
                    iterations=iterations,
                    branch=self.git.current_branch(),
                    final_commit=self.git.head_hash(),
                    action_needed="FIX_VALIDATION",
                    error_detail=json.dumps(failed_checks),
                )
        except PrePushValidationError as e:
            record.error_category = ErrorCategory.MANIFEST
            iterations.append(record)
            return LoopReport(
                success=False,
                total_iterations=1,
                iterations=iterations,
                branch=self.git.current_branch(),
                final_commit=self.git.head_hash(),
                action_needed="FIX_VALIDATION",
                error_detail=str(e),
            )

        # ── Step 3: Push to Apps Script ──────────────────────
        push_result = self.clasp.push()
        record.push_result = push_result

        if not push_result.success:
            record.error_category = classify_error(push_result.stderr)
            iterations.append(record)
            return LoopReport(
                success=False,
                total_iterations=1,
                iterations=iterations,
                branch=self.git.current_branch(),
                final_commit=self.git.head_hash(),
                action_needed="FIX_PUSH_ERROR",
                error_detail=push_result.stderr,
            )

        # ── Step 4: Wait for propagation ─────────────────────
        time.sleep(log_wait)

        # ── Step 5: Run tests ────────────────────────────────
        run_result = self.clasp.run(self.config.test_runner_function)

        if not run_result.success:
            # Execution itself failed (not a test failure)
            record.error_category = classify_error(run_result.stderr)
            iterations.append(record)
            return LoopReport(
                success=False,
                total_iterations=1,
                iterations=iterations,
                branch=self.git.current_branch(),
                final_commit=self.git.head_hash(),
                action_needed="FIX_RUNTIME_ERROR",
                error_detail=run_result.stderr,
            )

        # ── Step 6: Parse test results ───────────────────────
        test_report = parse_test_output(run_result.stdout)
        record.test_report = test_report

        if test_report.success:
            # All tests passed!
            if not self.git.is_clean():
                self.git.add_all()
                self.git._git(
                    ["commit", "-m",
                     f"test(pass): all {test_report.total} tests pass"]
                )
            record.committed = True
            record.commit_hash = self.git.head_hash()
            self.git.push()

            iterations.append(record)
            return LoopReport(
                success=True,
                total_iterations=1,
                iterations=iterations,
                branch=self.git.current_branch(),
                final_commit=self.git.head_hash(),
            )
        else:
            # Tests failed
            record.error_category = ErrorCategory.UNKNOWN
            # Classify based on first failing test
            for detail in test_report.details:
                if detail.status.value in ("FAIL", "ERROR"):
                    record.error_category = classify_error(detail.message)
                    break

            iterations.append(record)
            return LoopReport(
                success=False,
                total_iterations=1,
                iterations=iterations,
                branch=self.git.current_branch(),
                final_commit=self.git.head_hash(),
                action_needed="FIX_TEST_FAILURE",
                error_detail=test_report.to_json(),
            )

    def _validate_pre_push(self) -> list[dict]:
        """
        Run pre-push validation checks.

        Returns a list of check results, each with:
            {"check": str, "passed": bool, "detail": str}
        """
        checks: list[dict] = []

        # 1. Not on main
        branch = self.git.current_branch()
        is_main = branch == self.config.main_branch
        checks.append({
            "check": "not_on_main",
            "passed": not is_main,
            "detail": f"Current branch: {branch}",
        })

        # 2. clasp config exists
        clasp_json = self.project_root / ".clasp.json"
        checks.append({
            "check": "clasp_config_exists",
            "passed": clasp_json.exists(),
            "detail": str(clasp_json),
        })

        # 3. Script ID matches environment
        if clasp_json.exists():
            active_id = self._read_script_id(clasp_json)
            expected_config_name = (
                self.config.prod_config if is_main else self.config.dev_config
            )
            expected_config_path = self.project_root / expected_config_name
            if expected_config_path.exists():
                expected_id = self._read_script_id(expected_config_path)
                checks.append({
                    "check": "script_id_matches_env",
                    "passed": active_id == expected_id,
                    "detail": (
                        f"active={active_id[:12]}... "
                        f"expected={expected_id[:12]}..."
                    ),
                })
            else:
                checks.append({
                    "check": "script_id_matches_env",
                    "passed": False,
                    "detail": f"Expected config not found: {expected_config_path}",
                })

        # 4. Clean working tree
        clean = self.git.is_clean()
        checks.append({
            "check": "clean_working_tree",
            "passed": clean,
            "detail": "All changes committed" if clean else "Uncommitted changes",
        })

        # 5. Valid manifest
        manifest_path = self.project_root / "appsscript.json"
        mv = validate_manifest(manifest_path)
        checks.append({
            "check": "valid_manifest",
            "passed": mv.ok,
            "detail": mv.message,
        })
        if mv.warnings:
            for w in mv.warnings:
                checks.append({
                    "check": "manifest_warning",
                    "passed": True,  # Warnings don't block
                    "detail": w,
                })

        return checks

    @staticmethod
    def _read_script_id(config_path: Path) -> str:
        """Read the scriptId from a .clasp.json file."""
        with open(config_path) as f:
            data = json.load(f)
        return data.get("scriptId", "")
