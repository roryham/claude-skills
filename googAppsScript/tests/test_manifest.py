"""Tests for gas_skill.manifest."""
import json
from pathlib import Path

from gas_skill.manifest import validate, create_default, add_scope


class TestValidate:
    def test_valid_manifest(self, valid_manifest):
        result = validate(valid_manifest)
        assert result.ok is True
        assert result.message == "Manifest is valid"
        assert result.warnings == []

    def test_missing_file(self, tmp_path):
        result = validate(tmp_path / "nonexistent.json")
        assert result.ok is False
        assert "not found" in result.message

    def test_invalid_json(self, tmp_path):
        bad = tmp_path / "appsscript.json"
        bad.write_text("{bad json")
        result = validate(bad)
        assert result.ok is False
        assert "Invalid JSON" in result.message

    def test_missing_required_fields(self, tmp_path):
        m = tmp_path / "appsscript.json"
        m.write_text(json.dumps({"timeZone": "UTC"}))
        result = validate(m)
        assert result.ok is False
        assert "exceptionLogging" in result.message

    def test_non_v8_warning(self, tmp_path):
        m = tmp_path / "appsscript.json"
        m.write_text(json.dumps({
            "timeZone": "UTC",
            "exceptionLogging": "STACKDRIVER",
            "runtimeVersion": "DEPRECATED_ES5",
        }))
        result = validate(m)
        assert result.ok is True
        assert len(result.warnings) >= 1
        assert any("V8" in w for w in result.warnings)

    def test_non_stackdriver_warning(self, tmp_path):
        m = tmp_path / "appsscript.json"
        m.write_text(json.dumps({
            "timeZone": "UTC",
            "exceptionLogging": "CONSOLE",
            "runtimeVersion": "V8",
        }))
        result = validate(m)
        assert result.ok is True
        assert any("STACKDRIVER" in w for w in result.warnings)


class TestCreateDefault:
    def test_creates_file(self, tmp_path):
        p = tmp_path / "appsscript.json"
        create_default(p)
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["runtimeVersion"] == "V8"
        assert data["exceptionLogging"] == "STACKDRIVER"

    def test_custom_timezone(self, tmp_path):
        p = tmp_path / "appsscript.json"
        create_default(p, timezone="Europe/London")
        data = json.loads(p.read_text())
        assert data["timeZone"] == "Europe/London"


class TestAddScope:
    def test_add_new_scope(self, valid_manifest):
        add_scope(valid_manifest, "https://www.googleapis.com/auth/spreadsheets")
        data = json.loads(valid_manifest.read_text())
        assert "https://www.googleapis.com/auth/spreadsheets" in data["oauthScopes"]

    def test_no_duplicate(self, valid_manifest):
        scope = "https://www.googleapis.com/auth/spreadsheets"
        add_scope(valid_manifest, scope)
        add_scope(valid_manifest, scope)
        data = json.loads(valid_manifest.read_text())
        assert data["oauthScopes"].count(scope) == 1
