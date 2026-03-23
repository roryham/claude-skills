"""log_parser.py — Parse clasp output into structured data."""
from __future__ import annotations

import json
import re
from .models import (
    ErrorCategory,
    LogEntry,
    Severity,
    TestReport,
    TestResult,
    TestStatus,
)


# ── Error classification ──────────────────────────────────────

ERROR_PATTERNS: list[tuple[re.Pattern, ErrorCategory]] = [
    (re.compile(r"not logged in|401|token.*expired", re.I), ErrorCategory.AUTH),
    (re.compile(r"SyntaxError|Unexpected token", re.I), ErrorCategory.SYNTAX),
    (re.compile(r"ReferenceError|is not defined", re.I), ErrorCategory.REFERENCE),
    (re.compile(r"TypeError|is not a function|cannot read propert", re.I), ErrorCategory.TYPE),
    (re.compile(r"Invalid manifest|malformed", re.I), ErrorCategory.MANIFEST),
    (re.compile(r"quota|rate.?limit|RESOURCE_EXHAUSTED", re.I), ErrorCategory.QUOTA),
    (re.compile(r"exceeded maximum execution time|timeout|timed?\s*out", re.I), ErrorCategory.TIMEOUT),
    (re.compile(r"ECONNREFUSED|ETIMEDOUT|network|fetch.*fail", re.I), ErrorCategory.NETWORK),
    (re.compile(r"permission denied|403|insufficient.*scope", re.I), ErrorCategory.PERMISSION),
    (re.compile(r"script not found|404|not found", re.I), ErrorCategory.NOT_FOUND),
]


def classify_error(error_text: str) -> ErrorCategory:
    """Classify an error string into a known category."""
    for pattern, category in ERROR_PATTERNS:
        if pattern.search(error_text):
            return category
    return ErrorCategory.UNKNOWN


# ── Test output parsing ───────────────────────────────────────

def parse_test_output(clasp_stdout: str) -> TestReport:
    """
    Parse the JSON output from runAllTests into a TestReport.

    clasp run output format:
        > runAllTests
        {"total": 5, "passed": 4, ...}

    Or for errors:
        > runAllTests
        Exception: ReferenceError: x is not defined
    """
    lines = clasp_stdout.strip().splitlines()

    # Try to find JSON in the output
    json_str = ""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("{"):
            json_str = "\n".join(lines[i:])
            break

    if not json_str:
        # No JSON found — might be a runtime error
        error_text = clasp_stdout.strip()
        # Remove the "> functionName" prefix if present
        if error_text.startswith(">"):
            error_text = "\n".join(lines[1:]).strip()

        return TestReport(
            total=0,
            passed=0,
            failed=0,
            errors=1,
            success=False,
            details=[
                TestResult(
                    status=TestStatus.ERROR,
                    function="runAllTests",
                    message=f"No test output captured. Raw output: {error_text[:500]}",
                    timestamp="",
                    stack="",
                )
            ],
        )

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return TestReport(
            total=0,
            passed=0,
            failed=0,
            errors=1,
            success=False,
            details=[
                TestResult(
                    status=TestStatus.ERROR,
                    function="runAllTests",
                    message=f"Invalid JSON in test output: {e}",
                    timestamp="",
                    stack="",
                )
            ],
        )

    details = [
        TestResult(
            status=TestStatus(d.get("status", "ERROR")),
            function=d.get("function", "unknown"),
            message=d.get("message", ""),
            timestamp=d.get("timestamp", ""),
            stack=d.get("stack", ""),
        )
        for d in data.get("details", [])
    ]

    return TestReport(
        total=data.get("total", 0),
        passed=data.get("passed", 0),
        failed=data.get("failed", 0),
        errors=data.get("errors", 0),
        success=data.get("success", False),
        details=details,
    )


# ── Log entry parsing ─────────────────────────────────────────

def parse_log_entries(clasp_logs_output: str) -> list[LogEntry]:
    """
    Parse the output of `clasp logs --json` into LogEntry objects.

    clasp logs --json returns entries in the format:
    [
      {
        "timestamp": "2026-03-22T14:30:00.000Z",
        "severity": "ERROR",
        "textPayload": "ReferenceError: x is not defined at ..."
      },
      ...
    ]

    Or in some versions, one JSON object per line.
    """
    entries: list[LogEntry] = []

    if not clasp_logs_output.strip():
        return entries

    # Try parsing as JSON array first
    try:
        data = json.loads(clasp_logs_output)
        if isinstance(data, list):
            for item in data:
                entries.append(_parse_single_log(item))
            return entries
    except json.JSONDecodeError:
        pass

    # Try parsing as newline-delimited JSON
    for line in clasp_logs_output.strip().splitlines():
        line = line.strip()
        if not line or line.startswith(">"):
            continue
        try:
            item = json.loads(line)
            entries.append(_parse_single_log(item))
        except json.JSONDecodeError:
            # Not JSON — try to parse as plain text log
            entry = _parse_plain_log_line(line)
            if entry:
                entries.append(entry)

    return entries


def _parse_single_log(item: dict) -> LogEntry:
    """Parse a single JSON log object into a LogEntry."""
    message = item.get("textPayload", item.get("message", ""))
    severity_str = item.get("severity", "INFO").upper()

    try:
        severity = Severity(severity_str)
    except ValueError:
        severity = Severity.INFO

    # Try to extract function name and stack trace from message
    function_name = ""
    stack_trace = ""

    # Pattern: "at functionName (File:line:col)"
    stack_match = re.search(r"at (\w+)\s*\(", message)
    if stack_match:
        function_name = stack_match.group(1)

    # If message contains newlines, the part after the first line is stack
    if "\n" in message:
        parts = message.split("\n", 1)
        message = parts[0]
        stack_trace = parts[1].strip()

    return LogEntry(
        timestamp=item.get("timestamp", ""),
        severity=severity,
        message=message,
        function_name=function_name,
        stack_trace=stack_trace,
    )


def _parse_plain_log_line(line: str) -> LogEntry | None:
    """
    Attempt to parse a plain text log line.

    Expected format: "TIMESTAMP SEVERITY MESSAGE"
    Example: "2026-03-22 14:30:00 ERROR ReferenceError: x is not defined"
    """
    # Pattern: date time severity message
    pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[.\d]*Z?)\s+"
        r"(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+"
        r"(.+)",
        re.I,
    )
    match = pattern.match(line)
    if match:
        try:
            severity = Severity(match.group(2).upper())
        except ValueError:
            severity = Severity.INFO

        return LogEntry(
            timestamp=match.group(1),
            severity=severity,
            message=match.group(3),
        )

    return None
