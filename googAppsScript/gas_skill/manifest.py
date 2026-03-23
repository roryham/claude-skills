"""manifest.py — Manage appsscript.json manifest file."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ManifestValidation:
    """Result of manifest validation."""
    ok: bool
    message: str
    warnings: list[str]


# Required fields in appsscript.json
REQUIRED_FIELDS = {"timeZone", "exceptionLogging"}

# Default manifest for new projects
DEFAULT_MANIFEST = {
    "timeZone": "America/New_York",
    "dependencies": {},
    "exceptionLogging": "STACKDRIVER",
    "runtimeVersion": "V8",
    "oauthScopes": []
}


def validate(manifest_path: Path) -> ManifestValidation:
    """
    Validate an appsscript.json file.

    Checks:
    1. File exists
    2. File is valid JSON
    3. Required fields are present
    4. runtimeVersion is V8
    5. exceptionLogging is STACKDRIVER (recommended for log capture)
    """
    warnings: list[str] = []

    if not manifest_path.exists():
        return ManifestValidation(
            ok=False,
            message=f"Manifest not found: {manifest_path}",
            warnings=warnings,
        )

    try:
        with open(manifest_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return ManifestValidation(
            ok=False,
            message=f"Invalid JSON in manifest: {e}",
            warnings=warnings,
        )

    # Check required fields
    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        return ManifestValidation(
            ok=False,
            message=f"Missing required fields: {', '.join(sorted(missing))}",
            warnings=warnings,
        )

    # Check runtime version
    if data.get("runtimeVersion") != "V8":
        warnings.append(
            f"runtimeVersion is '{data.get('runtimeVersion')}', "
            "expected 'V8' for modern JavaScript support"
        )

    # Check exception logging
    if data.get("exceptionLogging") != "STACKDRIVER":
        warnings.append(
            "exceptionLogging should be 'STACKDRIVER' for clasp logs to work"
        )

    return ManifestValidation(
        ok=True,
        message="Manifest is valid",
        warnings=warnings,
    )


def create_default(manifest_path: Path, timezone: str = "America/New_York") -> None:
    """Create a default appsscript.json."""
    manifest = DEFAULT_MANIFEST.copy()
    manifest["timeZone"] = timezone
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def add_scope(manifest_path: Path, scope: str) -> None:
    """Add an OAuth scope to the manifest if not already present."""
    with open(manifest_path) as f:
        data = json.load(f)

    scopes = data.get("oauthScopes", [])
    if scope not in scopes:
        scopes.append(scope)
        data["oauthScopes"] = scopes
        with open(manifest_path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
