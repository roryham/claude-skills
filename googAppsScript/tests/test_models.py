"""Tests for gas_skill.models."""
import json

from gas_skill.models import (
    CommandResult,
    ErrorCategory,
    IterationRecord,
    LogEntry,
    LoopReport,
    ProjectStatus,
    Severity,
    TestReport,
    TestResult,
    TestStatus,
)


class TestEnums:
    def test_error_category_values(self):
        assert ErrorCategory.AUTH.value == "AUTH"
        assert ErrorCategory.UNKNOWN.value == "UNKNOWN"
        assert ErrorCategory.PERMISSION.value == "PERMISSION"
        assert ErrorCategory.NOT_FOUND.value == "NOT_FOUND"

    def test_test_status_values(self):
        assert TestStatus.PASS.value == "PASS"
        assert TestStatus.FAIL.value == "FAIL"
        assert TestStatus.ERROR.value == "ERROR"

    def test_severity_values(self):
        assert Severity.DEBUG.value == "DEBUG"
        assert Severity.CRITICAL.value == "CRITICAL"

    def test_enum_str_comparison(self):
        assert ErrorCategory.AUTH == "AUTH"
        assert TestStatus.PASS == "PASS"
        assert Severity.INFO == "INFO"


class TestCommandResult:
    def test_construction(self):
        r = CommandResult(
            command="git status",
            exit_code=0,
            stdout="clean",
            stderr="",
            success=True,
            duration_sec=0.1,
        )
        assert r.success is True
        assert r.exit_code == 0

    def test_to_dict(self):
        r = CommandResult("cmd", 0, "out", "err", True, 1.5)
        d = r.to_dict()
        assert d["command"] == "cmd"
        assert d["success"] is True

    def test_to_json(self):
        r = CommandResult("cmd", 0, "out", "", True, 0.5)
        j = r.to_json()
        data = json.loads(j)
        assert data["command"] == "cmd"


class TestTestReport:
    def test_summary(self):
        report = TestReport(total=5, passed=3, failed=1, errors=1, success=False)
        assert report.summary == "3/5 passed, 1 failed, 1 errors"

    def test_failing_tests(self):
        details = [
            TestResult(status=TestStatus.PASS, function="t1", message="ok"),
            TestResult(status=TestStatus.FAIL, function="t2", message="bad"),
            TestResult(status=TestStatus.ERROR, function="t3", message="err"),
        ]
        report = TestReport(total=3, passed=1, failed=1, errors=1, success=False, details=details)
        failing = report.failing_tests
        assert len(failing) == 2
        assert failing[0].function == "t2"
        assert failing[1].function == "t3"

    def test_to_dict(self):
        report = TestReport(total=1, passed=1, failed=0, errors=0, success=True,
                            details=[TestResult(status=TestStatus.PASS, function="t1",
                                                message="ok")])
        d = report.to_dict()
        assert d["success"] is True
        assert d["details"][0]["status"] == "PASS"

    def test_to_json(self):
        report = TestReport(total=0, passed=0, failed=0, errors=0, success=True)
        data = json.loads(report.to_json())
        assert data["success"] is True


class TestIterationRecord:
    def test_to_dict_no_nested(self):
        rec = IterationRecord(iteration=1)
        d = rec.to_dict()
        assert d["iteration"] == 1
        assert d["push_result"] is None
        assert d["test_report"] is None

    def test_to_dict_with_nested(self):
        rec = IterationRecord(
            iteration=2,
            push_result=CommandResult("push", 0, "ok", "", True, 1.0),
            test_report=TestReport(total=1, passed=1, failed=0, errors=0, success=True),
        )
        d = rec.to_dict()
        assert d["push_result"]["command"] == "push"
        assert d["test_report"]["success"] is True


class TestLoopReport:
    def test_to_json(self):
        report = LoopReport(success=True, total_iterations=1, branch="feature/x")
        data = json.loads(report.to_json())
        assert data["success"] is True
        assert data["branch"] == "feature/x"


class TestLogEntry:
    def test_to_dict(self):
        entry = LogEntry(timestamp="2026-01-01", severity=Severity.ERROR, message="fail")
        d = entry.to_dict()
        assert d["severity"] == "ERROR"


class TestProjectStatus:
    def test_to_dict(self):
        ps = ProjectStatus(branch="main", environment="prod")
        d = ps.to_dict()
        assert d["branch"] == "main"
        assert d["environment"] == "prod"
