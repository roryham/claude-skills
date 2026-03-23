"""changelog.py — Manage CHANGELOG.md following Keep a Changelog format."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path


INITIAL_CHANGELOG = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

"""

SECTION_HEADERS = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")

# Map commit types to changelog sections
TYPE_TO_SECTION = {
    "feat": "Added",
    "fix": "Fixed",
    "refactor": "Changed",
    "perf": "Changed",
    "docs": "Changed",
    "chore": "Changed",
    "style": "Changed",
    "test": "Changed",
}


def create_initial(changelog_path: Path) -> None:
    """Create an initial CHANGELOG.md."""
    changelog_path.write_text(INITIAL_CHANGELOG)


def add_entry(
    changelog_path: Path,
    commit_type: str,
    description: str,
) -> None:
    """
    Add an entry to the [Unreleased] section of CHANGELOG.md.

    The entry is placed under the appropriate subsection header
    (Added, Fixed, Changed, etc.) based on the commit type.
    """
    if not changelog_path.exists():
        create_initial(changelog_path)

    content = changelog_path.read_text()
    section = TYPE_TO_SECTION.get(commit_type, "Changed")

    # Find [Unreleased] section
    unreleased_pattern = re.compile(r"(## \[Unreleased\]\n)", re.MULTILINE)
    match = unreleased_pattern.search(content)

    if not match:
        # No [Unreleased] section found; insert one after the header
        header_end = content.find("\n\n") + 2
        content = (
            content[:header_end]
            + "## [Unreleased]\n\n"
            + content[header_end:]
        )
        match = unreleased_pattern.search(content)

    # Find or create the subsection (e.g., ### Added) within [Unreleased]
    unreleased_start = match.end()

    # Find the end of the [Unreleased] section (next ## heading or EOF)
    next_version = re.search(r"\n## \[", content[unreleased_start:])
    if next_version:
        unreleased_end = unreleased_start + next_version.start()
    else:
        unreleased_end = len(content)

    unreleased_block = content[unreleased_start:unreleased_end]

    subsection_pattern = re.compile(rf"(### {section}\n)", re.MULTILINE)
    sub_match = subsection_pattern.search(unreleased_block)

    entry_line = f"- {description}\n"

    if sub_match:
        # Insert after the subsection header
        insert_pos = unreleased_start + sub_match.end()
        content = content[:insert_pos] + entry_line + content[insert_pos:]
    else:
        # Create the subsection at the end of [Unreleased]
        new_subsection = f"\n### {section}\n{entry_line}"
        content = (
            content[:unreleased_end]
            + new_subsection
            + content[unreleased_end:]
        )

    changelog_path.write_text(content)


def finalize_release(
    changelog_path: Path,
    version: str,
    release_date: date | None = None,
) -> None:
    """
    Move all [Unreleased] entries under a new version heading.

    Before:
        ## [Unreleased]
        ### Added
        - New feature

    After:
        ## [Unreleased]

        ## [1.2.0] - 2026-03-22
        ### Added
        - New feature
    """
    if release_date is None:
        release_date = date.today()

    content = changelog_path.read_text()

    # Extract [Unreleased] content
    unreleased_header = re.compile(r"## \[Unreleased\]\n", re.MULTILINE)
    match = unreleased_header.search(content)

    if not match:
        return

    unreleased_start = match.end()

    # Find next version heading
    next_version = re.search(r"\n## \[", content[unreleased_start:])
    if next_version:
        unreleased_end = unreleased_start + next_version.start()
    else:
        unreleased_end = len(content)

    unreleased_content = content[unreleased_start:unreleased_end].strip()

    if not unreleased_content:
        return  # Nothing to release

    # Build new version section
    version_heading = f"## [{version}] - {release_date.isoformat()}"
    new_section = f"\n\n{version_heading}\n{unreleased_content}\n"

    # Replace: clear [Unreleased] and insert new version section
    new_content = (
        content[:unreleased_start]
        + "\n"
        + new_section
        + content[unreleased_end:]
    )

    changelog_path.write_text(new_content)


def get_release_notes(changelog_path: Path, version: str) -> str:
    """
    Extract the changelog entries for a specific version.

    Returns the content between the version heading and the next
    version heading (or EOF), suitable for GitHub release notes.
    """
    content = changelog_path.read_text()

    version_pattern = re.compile(
        rf"## \[{re.escape(version)}\].*?\n(.*?)(?=\n## \[|\Z)",
        re.DOTALL,
    )
    match = version_pattern.search(content)

    if match:
        return match.group(1).strip()
    return f"Release {version}"
