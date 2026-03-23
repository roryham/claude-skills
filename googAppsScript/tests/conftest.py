"""Shared test fixtures."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gas_skill.config import ProjectConfig


@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory with basic structure."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Code.js").write_text("function hello() { return 'hi'; }\n")
    return tmp_path


@pytest.fixture
def mock_config(tmp_project_dir: Path) -> ProjectConfig:
    """Create a ProjectConfig pointing at the temp dir."""
    return ProjectConfig(project_root=tmp_project_dir)


@pytest.fixture
def mock_clasp_json(tmp_project_dir: Path) -> Path:
    """Create a .clasp.json in the temp project dir."""
    clasp_json = tmp_project_dir / ".clasp.json"
    clasp_json.write_text(json.dumps({
        "scriptId": "test-script-id-12345",
        "rootDir": "src",
    }))
    return clasp_json


@pytest.fixture
def mock_clasp_dev_json(tmp_project_dir: Path) -> Path:
    """Create a .clasp.dev.json in the temp project dir."""
    clasp_dev = tmp_project_dir / ".clasp.dev.json"
    clasp_dev.write_text(json.dumps({
        "scriptId": "test-script-id-12345",
        "rootDir": "src",
    }))
    return clasp_dev


@pytest.fixture
def mock_clasp_prod_json(tmp_project_dir: Path) -> Path:
    """Create a .clasp.prod.json in the temp project dir."""
    clasp_prod = tmp_project_dir / ".clasp.prod.json"
    clasp_prod.write_text(json.dumps({
        "scriptId": "prod-script-id-99999",
        "rootDir": "src",
    }))
    return clasp_prod


@pytest.fixture
def valid_manifest(tmp_project_dir: Path) -> Path:
    """Create a valid appsscript.json."""
    manifest_path = tmp_project_dir / "appsscript.json"
    manifest_path.write_text(json.dumps({
        "timeZone": "America/New_York",
        "dependencies": {},
        "exceptionLogging": "STACKDRIVER",
        "runtimeVersion": "V8",
        "oauthScopes": [],
    }, indent=2))
    return manifest_path
