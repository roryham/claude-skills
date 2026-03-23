# gas-skill

A Python CLI tool that enables [Claude Code](https://claude.com/claude-code) to autonomously manage Google Apps Script (GAS) projects. It wraps `clasp` and `git` commands, providing structured JSON output for every operation and supporting the full development lifecycle: scaffolding, branching, code push, remote execution, automated testing, merging, and production releases.

## What it does

- **Scaffolds** new Apps Script projects with dual environments (production + development)
- **Pushes** local JavaScript to Google Apps Script via `clasp`
- **Runs** remote functions and captures structured results
- **Tests** code through an automated push-run-evaluate feedback loop
- **Manages** Git branches with safety enforcement (no direct commits to `main`)
- **Merges** branches with post-merge test verification
- **Releases** to production with tagging, deployment, smoke tests, and automatic rollback on failure
- **Classifies** errors into actionable categories (AUTH, SYNTAX, REFERENCE, TIMEOUT, etc.)

All output is JSON, so Claude Code can parse results and make intelligent decisions.

## Requirements

| Tool | Version | Purpose |
|---|---|---|
| Python | >= 3.11 | Runtime |
| Node.js | >= 18 | Required by clasp |
| clasp | >= 2.4 | Google Apps Script CLI |
| Git | >= 2.39 | Version control |
| GitHub CLI (gh) | >= 2.0 | GitHub operations |

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd <project-dir>

# Create a virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Verify
gas-skill --help
```

## Quick start

```bash
# 1. Check that all prerequisites are installed and authenticated
gas-skill preflight

# 2. Initialize a new project (creates prod + dev Apps Script projects)
gas-skill init --type sheets --title "My Project" --github-url git@github.com:user/repo.git

# 3. Create a feature branch
gas-skill branch create add-email-report

# 4. Write code in src/, then commit
gas-skill commit -m "add email report generator" --type feat --scope reports

# 5. Push to Apps Script and run tests
gas-skill test-loop

# 6. If tests fail, fix code, commit, and test-loop again

# 7. Merge to develop when tests pass
gas-skill merge --from feature/add-email-report --to develop

# 8. Release to production
gas-skill release --version 1.0.0 --summary "Initial release"
```

## Commands

| Command | Description |
|---|---|
| `preflight` | Validate all prerequisites |
| `init` | Scaffold a new project |
| `status` | Show branch, environment, and sync status |
| `branch` | Create, switch, list, or delete branches |
| `commit` | Create a conventional commit with changelog update |
| `push` | Push code to Apps Script |
| `run` | Execute a remote function |
| `test-loop` | Push, run tests, and report results |
| `logs` | Retrieve and parse execution logs |
| `merge` | Merge branches with post-merge testing |
| `release` | Full production release with rollback safety |
| `hotfix` | Create and finish hotfix branches |

## Documentation

- **[Quickstart Guide](docs/quickstart.md)** - Get up and running in 10 minutes
- **[User Guide](docs/user-guide.md)** - Complete reference for all commands and workflows
- **[Specification](SPECIFICATION.org)** - Full functional specification

## Project structure

```
gas_skill/             Python package (the CLI tool)
  gas_skill.py         CLI entrypoint with argparse
  git_manager.py       Git operations with branch safety
  clasp_wrapper.py     clasp CLI wrapper
  log_parser.py        Error classification + test/log parsing
  runner.py            Feedback loop engine
  config.py            Configuration from gas_skill.toml
  manifest.py          appsscript.json management
  changelog.py         CHANGELOG.md management
  models.py            Dataclasses and enums
  exceptions.py        Exception hierarchy
  _subprocess.py       Subprocess execution wrapper
tests/                 Unit tests (102 tests)
.claude/skills/        Claude Code skill definition
```

## How it works with Claude Code

The `.claude/skills/gas-integration.md` skill file registers this tool with Claude Code. When activated, Claude Code uses `gas-skill` commands instead of calling `clasp` or `git` directly. The JSON output from every command gives Claude Code the structured information it needs to make decisions, diagnose errors, and iterate on fixes.

The key design principle: **Claude Code is the intelligent agent; gas-skill is the reliable executor.** The test-loop command performs a single push-run-evaluate cycle and returns results. Claude Code reads the structured error report, decides on a fix, edits files, and calls the loop again.

## License

MIT
