"""Tests for gas_skill.config."""
from pathlib import Path

from gas_skill.config import ProjectConfig


class TestProjectConfig:
    def test_defaults(self, tmp_path: Path):
        config = ProjectConfig(project_root=tmp_path)
        assert config.name == "gas-project"
        assert config.main_branch == "main"
        assert config.max_retries == 5
        assert config.root_dir == "src"

    def test_load_missing_file(self, tmp_path: Path):
        config = ProjectConfig.load(tmp_path)
        assert config.project_root == tmp_path
        assert config.name == "gas-project"

    def test_load_valid_toml(self, tmp_path: Path):
        toml_content = """\
[project]
name = "my-project"
description = "A test project"

[clasp]
root_dir = "source"

[test_loop]
max_retries = 10
retry_delay_sec = 5

[git]
main_branch = "master"
feature_prefix = "feat/"

[logging]
level = "DEBUG"
"""
        (tmp_path / "gas_skill.toml").write_text(toml_content)
        config = ProjectConfig.load(tmp_path)
        assert config.name == "my-project"
        assert config.description == "A test project"
        assert config.root_dir == "source"
        assert config.max_retries == 10
        assert config.retry_delay_sec == 5
        assert config.main_branch == "master"
        assert config.feature_prefix == "feat/"
        assert config.log_level == "DEBUG"

    def test_load_partial_config(self, tmp_path: Path):
        toml_content = """\
[project]
name = "partial"
"""
        (tmp_path / "gas_skill.toml").write_text(toml_content)
        config = ProjectConfig.load(tmp_path)
        assert config.name == "partial"
        assert config.max_retries == 5  # default
        assert config.main_branch == "main"  # default
