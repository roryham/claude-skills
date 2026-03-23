"""Tests for gas_skill.log_parser."""
import json

from gas_skill.log_parser import (
    classify_error,
    parse_log_entries,
    parse_test_output,
    _parse_plain_log_line,
)
from gas_skill.models import ErrorCategory, Severity, TestStatus


class TestClassifyError:
    def test_auth_error(self):
        assert classify_error("not logged in") == ErrorCategory.AUTH
        assert classify_error("Error 401 Unauthorized") == ErrorCategory.AUTH
        assert classify_error("token has expired") == ErrorCategory.AUTH

    def test_syntax_error(self):
        assert classify_error("SyntaxError: Unexpected token") == ErrorCategory.SYNTAX

    def test_reference_error(self):
        assert classify_error("ReferenceError: x is not defined") == ErrorCategory.REFERENCE

    def test_type_error(self):
        assert classify_error("TypeError: foo is not a function") == ErrorCategory.TYPE
        assert classify_error("cannot read property of null") == ErrorCategory.TYPE

    def test_manifest_error(self):
        assert classify_error("Invalid manifest file") == ErrorCategory.MANIFEST

    def test_quota_error(self):
        assert classify_error("RESOURCE_EXHAUSTED: quota limit") == ErrorCategory.QUOTA
        assert classify_error("rate limit exceeded") == ErrorCategory.QUOTA

    def test_timeout_error(self):
        assert classify_error("exceeded maximum execution time") == ErrorCategory.TIMEOUT
        assert classify_error("request timed out") == ErrorCategory.TIMEOUT

    def test_network_error(self):
        assert classify_error("ECONNREFUSED") == ErrorCategory.NETWORK
        assert classify_error("network error occurred") == ErrorCategory.NETWORK
        assert classify_error("fetch failed for URL") == ErrorCategory.NETWORK

    def test_permission_error(self):
        assert classify_error("permission denied") == ErrorCategory.PERMISSION
        assert classify_error("Error 403 Forbidden") == ErrorCategory.PERMISSION
        assert classify_error("insufficient scope for action") == ErrorCategory.PERMISSION

    def test_not_found_error(self):
        assert classify_error("script not found") == ErrorCategory.NOT_FOUND
        assert classify_error("Error 404 Not Found") == ErrorCategory.NOT_FOUND

    def test_unknown_error(self):
        assert classify_error("something completely different") == ErrorCategory.UNKNOWN
        assert classify_error("") == ErrorCategory.UNKNOWN


class TestParseTestOutput:
    def test_valid_json_output(self):
        output = """> runAllTests
{"total": 2, "passed": 2, "failed": 0, "errors": 0, "success": true, "details": [
  {"function": "test_a", "status": "PASS", "message": "OK", "timestamp": "2026-01-01", "stack": ""},
  {"function": "test_b", "status": "PASS", "message": "OK", "timestamp": "2026-01-01", "stack": ""}
]}"""
        report = parse_test_output(output)
        assert report.success is True
        assert report.total == 2
        assert report.passed == 2
        assert len(report.details) == 2
        assert report.details[0].status == TestStatus.PASS

    def test_failed_test_output(self):
        output = """> runAllTests
{"total": 2, "passed": 1, "failed": 1, "errors": 0, "success": false, "details": [
  {"function": "test_a", "status": "PASS", "message": "OK", "timestamp": "", "stack": ""},
  {"function": "test_b", "status": "FAIL", "message": "Expected 1 got 2", "timestamp": "", "stack": ""}
]}"""
        report = parse_test_output(output)
        assert report.success is False
        assert report.failed == 1
        assert report.details[1].status == TestStatus.FAIL

    def test_runtime_error(self):
        output = """> runAllTests
Exception: ReferenceError: myFunc is not defined"""
        report = parse_test_output(output)
        assert report.success is False
        assert report.errors == 1
        assert "No test output captured" in report.details[0].message

    def test_malformed_json(self):
        output = """> runAllTests
{invalid json here"""
        report = parse_test_output(output)
        assert report.success is False
        assert "Invalid JSON" in report.details[0].message

    def test_empty_output(self):
        report = parse_test_output("")
        assert report.success is False
        assert report.errors == 1


class TestParseLogEntries:
    def test_json_array(self):
        logs = json.dumps([
            {"timestamp": "2026-01-01T00:00:00Z", "severity": "ERROR",
             "textPayload": "ReferenceError: x"},
            {"timestamp": "2026-01-01T00:01:00Z", "severity": "INFO",
             "textPayload": "OK"},
        ])
        entries = parse_log_entries(logs)
        assert len(entries) == 2
        assert entries[0].severity == Severity.ERROR
        assert entries[1].severity == Severity.INFO

    def test_ndjson(self):
        logs = (
            '{"timestamp": "t1", "severity": "INFO", "textPayload": "msg1"}\n'
            '{"timestamp": "t2", "severity": "ERROR", "textPayload": "msg2"}\n'
        )
        entries = parse_log_entries(logs)
        assert len(entries) == 2

    def test_plain_text(self):
        logs = "2026-01-01 12:00:00 ERROR Something went wrong"
        entries = parse_log_entries(logs)
        assert len(entries) == 1
        assert entries[0].severity == Severity.ERROR
        assert "Something went wrong" in entries[0].message

    def test_empty_input(self):
        assert parse_log_entries("") == []
        assert parse_log_entries("   ") == []


class TestParsePlainLogLine:
    def test_valid_line(self):
        entry = _parse_plain_log_line("2026-03-22 14:30:00 ERROR bad thing")
        assert entry is not None
        assert entry.severity == Severity.ERROR
        assert entry.message == "bad thing"

    def test_invalid_line(self):
        assert _parse_plain_log_line("not a log line") is None
