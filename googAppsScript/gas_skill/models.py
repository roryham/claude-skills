"""models.py — Data models for gas-skill."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


# ── Enums ──────────────────────────────────────────────────────

class ErrorCategory(str, Enum):
    """Classification of errors from clasp operations."""
    AUTH = "AUTH"
    REFERENCE = "REFERENCE"
    TYPE = "TYPE"
    SYNTAX = "SYNTAX"
    MANIFEST = "MANIFEST"
    QUOTA = "QUOTA"
    TIMEOUT = "TIMEOUT"
    NETWORK = "NETWORK"
    PERMISSION = "PERMISSION"
    NOT_FOUND = "NOT_FOUND"
    UNKNOWN = "UNKNOWN"


class TestStatus(str, Enum):
    """Status of an individual test."""
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"


class Severity(str, Enum):
    """Log entry severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ── Command Result ─────────────────────────────────────────────

@dataclass
class CommandResult:
    """Result of executing an external command."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    success: bool
    duration_sec: float

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ── Test Models ────────────────────────────────────────────────

@dataclass
class TestResult:
    """Result of a single test function."""
    status: TestStatus
    function: str
    message: str
    timestamp: str = ""
    stack: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class TestReport:
    """Aggregated test results from runAllTests."""
    total: int
    passed: int
    failed: int
    errors: int
    success: bool
    details: list[TestResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "success": self.success,
            "details": [d.to_dict() for d in self.details],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @property
    def failing_tests(self) -> list[TestResult]:
        """Return only failed and errored tests."""
        return [
            d for d in self.details
            if d.status in (TestStatus.FAIL, TestStatus.ERROR)
        ]

    @property
    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"{self.passed}/{self.total} passed, "
            f"{self.failed} failed, "
            f"{self.errors} errors"
        )


# ── Log Models ─────────────────────────────────────────────────

@dataclass
class LogEntry:
    """A single log entry from Apps Script execution."""
    timestamp: str = ""
    severity: Severity = Severity.INFO
    message: str = ""
    function_name: str = ""
    stack_trace: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


# ── Iteration Models ──────────────────────────────────────────

@dataclass
class IterationRecord:
    """Record of a single push-run-evaluate cycle."""
    iteration: int = 0
    committed: bool = False
    commit_hash: str = ""
    push_result: CommandResult | None = None
    test_report: TestReport | None = None
    error_category: ErrorCategory = ErrorCategory.UNKNOWN

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "committed": self.committed,
            "commit_hash": self.commit_hash,
            "push_result": self.push_result.to_dict() if self.push_result else None,
            "test_report": self.test_report.to_dict() if self.test_report else None,
            "error_category": self.error_category.value,
        }


@dataclass
class LoopReport:
    """Complete report from a feedback loop execution."""
    success: bool
    total_iterations: int
    iterations: list[IterationRecord] = field(default_factory=list)
    branch: str = ""
    final_commit: str = ""
    action_needed: str = ""
    error_detail: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "total_iterations": self.total_iterations,
            "iterations": [i.to_dict() for i in self.iterations],
            "branch": self.branch,
            "final_commit": self.final_commit,
            "action_needed": self.action_needed,
            "error_detail": self.error_detail,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ── Project Status Model ──────────────────────────────────────

@dataclass
class ProjectStatus:
    """Comprehensive project status."""
    branch: str = ""
    environment: str = "dev"
    script_id: str = ""
    clean_tree: bool = True
    uncommitted_files: list[str] = field(default_factory=list)
    latest_commit_hash: str = ""
    latest_commit_message: str = ""
    latest_tag: str = ""
    ahead: int = 0
    behind: int = 0
    local_branches: list[str] = field(default_factory=list)
    remote_branches: list[str] = field(default_factory=list)
    clasp_config_valid: bool = False
    clasp_config_env_match: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
