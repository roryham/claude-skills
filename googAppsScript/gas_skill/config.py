"""config.py — Project configuration from gas_skill.toml."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 12):
    import tomllib
else:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]


@dataclass
class ProjectConfig:
    """All configuration for the gas-skill orchestrator."""

    # Paths
    project_root: Path = field(default_factory=Path.cwd)

    # Project metadata
    name: str = "gas-project"
    description: str = ""

    # clasp
    root_dir: str = "src"
    prod_config: str = ".clasp.prod.json"
    dev_config: str = ".clasp.dev.json"

    # Test loop
    max_retries: int = 5
    retry_delay_sec: int = 2
    log_wait_sec: int = 3
    test_runner_function: str = "runAllTests"

    # Git
    remote: str = "origin"
    main_branch: str = "main"
    develop_branch: str = "develop"
    feature_prefix: str = "feature/"
    bugfix_prefix: str = "bugfix/"
    hotfix_prefix: str = "hotfix/"
    experiment_prefix: str = "experiment/"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    @classmethod
    def load(cls, project_root: Path | None = None) -> ProjectConfig:
        """Load configuration from gas_skill.toml in the project root."""
        root = project_root or Path.cwd()
        config_file = root / "gas_skill.toml"

        if not config_file.exists():
            return cls(project_root=root)

        with open(config_file, "rb") as f:
            data = tomllib.load(f)

        project = data.get("project", {})
        clasp = data.get("clasp", {})
        test_loop = data.get("test_loop", {})
        git = data.get("git", {})
        logging = data.get("logging", {})

        return cls(
            project_root=root,
            name=project.get("name", "gas-project"),
            description=project.get("description", ""),
            root_dir=clasp.get("root_dir", "src"),
            prod_config=clasp.get("prod_config", ".clasp.prod.json"),
            dev_config=clasp.get("dev_config", ".clasp.dev.json"),
            max_retries=test_loop.get("max_retries", 5),
            retry_delay_sec=test_loop.get("retry_delay_sec", 2),
            log_wait_sec=test_loop.get("log_wait_sec", 3),
            test_runner_function=test_loop.get("test_runner_function", "runAllTests"),
            remote=git.get("remote", "origin"),
            main_branch=git.get("main_branch", "main"),
            develop_branch=git.get("develop_branch", "develop"),
            feature_prefix=git.get("feature_prefix", "feature/"),
            bugfix_prefix=git.get("bugfix_prefix", "bugfix/"),
            hotfix_prefix=git.get("hotfix_prefix", "hotfix/"),
            experiment_prefix=git.get("experiment_prefix", "experiment/"),
            log_level=logging.get("level", "INFO"),
            log_format=logging.get("format", "json"),
        )
