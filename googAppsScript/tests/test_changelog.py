"""Tests for gas_skill.changelog."""
from datetime import date
from pathlib import Path

from gas_skill.changelog import (
    create_initial,
    add_entry,
    finalize_release,
    get_release_notes,
)


class TestCreateInitial:
    def test_creates_file(self, tmp_path):
        p = tmp_path / "CHANGELOG.md"
        create_initial(p)
        assert p.exists()
        content = p.read_text()
        assert "# Changelog" in content
        assert "[Unreleased]" in content


class TestAddEntry:
    def test_add_feat(self, tmp_path):
        p = tmp_path / "CHANGELOG.md"
        create_initial(p)
        add_entry(p, "feat", "New feature X")
        content = p.read_text()
        assert "### Added" in content
        assert "- New feature X" in content

    def test_add_fix(self, tmp_path):
        p = tmp_path / "CHANGELOG.md"
        create_initial(p)
        add_entry(p, "fix", "Fix bug Y")
        content = p.read_text()
        assert "### Fixed" in content
        assert "- Fix bug Y" in content

    def test_add_multiple_same_section(self, tmp_path):
        p = tmp_path / "CHANGELOG.md"
        create_initial(p)
        add_entry(p, "feat", "Feature A")
        add_entry(p, "feat", "Feature B")
        content = p.read_text()
        assert content.count("### Added") == 1
        assert "- Feature A" in content
        assert "- Feature B" in content

    def test_add_creates_changelog_if_missing(self, tmp_path):
        p = tmp_path / "CHANGELOG.md"
        add_entry(p, "feat", "New thing")
        assert p.exists()
        assert "- New thing" in p.read_text()


class TestFinalizeRelease:
    def test_finalize(self, tmp_path):
        p = tmp_path / "CHANGELOG.md"
        create_initial(p)
        add_entry(p, "feat", "Feature A")
        finalize_release(p, "1.0.0", release_date=date(2026, 3, 22))
        content = p.read_text()
        assert "[1.0.0] - 2026-03-22" in content
        assert "- Feature A" in content

    def test_finalize_empty_unreleased(self, tmp_path):
        p = tmp_path / "CHANGELOG.md"
        create_initial(p)
        finalize_release(p, "1.0.0")
        content = p.read_text()
        # Should not add version if nothing unreleased
        assert "[1.0.0]" not in content

    def test_unreleased_section_cleared(self, tmp_path):
        p = tmp_path / "CHANGELOG.md"
        create_initial(p)
        add_entry(p, "feat", "Thing")
        finalize_release(p, "1.0.0", release_date=date(2026, 1, 1))
        content = p.read_text()
        assert "[Unreleased]" in content  # header remains


class TestGetReleaseNotes:
    def test_get_notes(self, tmp_path):
        p = tmp_path / "CHANGELOG.md"
        create_initial(p)
        add_entry(p, "feat", "Cool feature")
        finalize_release(p, "2.0.0", release_date=date(2026, 3, 22))
        notes = get_release_notes(p, "2.0.0")
        assert "Cool feature" in notes

    def test_missing_version(self, tmp_path):
        p = tmp_path / "CHANGELOG.md"
        create_initial(p)
        notes = get_release_notes(p, "9.9.9")
        assert "Release 9.9.9" in notes
