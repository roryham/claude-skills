# User Guide

Complete reference for the `gas-skill` CLI tool.

## Table of Contents

- [Overview](#overview)
- [Configuration](#configuration)
- [Commands](#commands)
  - [preflight](#preflight)
  - [init](#init)
  - [status](#status)
  - [branch](#branch)
  - [commit](#commit)
  - [push](#push)
  - [run](#run)
  - [test-loop](#test-loop)
  - [logs](#logs)
  - [merge](#merge)
  - [release](#release)
  - [hotfix](#hotfix)
- [Branching Strategy](#branching-strategy)
- [Dual Environment Model](#dual-environment-model)
- [Test Harness](#test-harness)
- [Error Classification](#error-classification)
- [Feedback Loop Architecture](#feedback-loop-architecture)
- [Changelog Management](#changelog-management)
- [Troubleshooting](#troubleshooting)

---

## Overview

`gas-skill` is a Python CLI that wraps `clasp` (Google Apps Script CLI) and `git` to provide a structured, automated development workflow. Every command outputs JSON to stdout, making it suitable for both human use and programmatic consumption by Claude Code.

### Global options

```
gas-skill [--project-root PATH] <command> [options]
```

| Option | Description |
|---|---|
| `--project-root PATH` | Project root directory. Defaults to the current working directory. |

### Running the tool

```bash
# If installed with pip install -e .
gas-skill <command>

# Or run as a Python module
python -m gas_skill <command>
```

---

## Configuration

Project settings are stored in `gas_skill.toml` at the project root. This file is created by `gas-skill init` and can be edited manually.

### Full configuration reference

```toml
[project]
name = "my-gas-project"             # Project name (used in output)
description = "Project description"  # Optional description

[clasp]
root_dir = "src"                     # Directory containing .js source files
prod_config = ".clasp.prod.json"     # Production clasp config filename
dev_config = ".clasp.dev.json"       # Development clasp config filename

[test_loop]
max_retries = 5                      # Max push-run-fix cycles before giving up
retry_delay_sec = 2                  # Seconds to wait between retries
log_wait_sec = 3                     # Seconds to wait after push for log propagation
test_runner_function = "runAllTests" # GAS function that runs the test suite

[git]
remote = "origin"                    # Git remote name
main_branch = "main"                 # Production branch name
develop_branch = "develop"           # Integration branch name
feature_prefix = "feature/"          # Prefix for feature branches
bugfix_prefix = "bugfix/"            # Prefix for bugfix branches
hotfix_prefix = "hotfix/"            # Prefix for hotfix branches
experiment_prefix = "experiment/"    # Prefix for experiment branches

[logging]
level = "INFO"                       # Log level: DEBUG, INFO, WARNING, ERROR
format = "json"                      # Output format: json, text
```

### Defaults

If `gas_skill.toml` does not exist, all settings use the defaults shown above. The tool will still function — it only requires the config file for customized projects.

---

## Commands

### preflight

Validate that all prerequisites are installed and authenticated.

```bash
gas-skill preflight
```

**Checks performed:**

1. Python version >= 3.11
2. Node.js installed
3. `clasp` installed
4. Git installed
5. GitHub CLI (`gh`) installed and authenticated
6. `~/.clasprc.json` exists (clasp authenticated)
7. `gas_skill.toml` exists
8. `appsscript.json` exists and is valid

**Output:**

```json
{
  "all_passed": false,
  "checks": [
    {"name": "python", "passed": true, "detail": "3.13.5"},
    {"name": "clasp", "passed": false, "detail": "Command not found: clasp"},
    ...
  ]
}
```

**When to use:** Run this before starting any work to make sure your environment is correctly set up. Fix any failing checks before proceeding.

---

### init

Scaffold a complete new project from scratch.

```bash
gas-skill init --type <type> --title "<name>" --github-url <url>
```

| Option | Required | Description |
|---|---|---|
| `--type` | Yes | Apps Script project type: `sheets`, `docs`, `slides`, `forms`, `webapp`, `api` |
| `--title` | Yes | Project title (used for the Apps Script project name) |
| `--github-url` | Yes | GitHub remote URL (SSH or HTTPS) |

**What it does:**

1. Creates a **production** Apps Script project and saves its config as `.clasp.prod.json`
2. Creates a **development** Apps Script project (titled "... [DEV]") and saves as `.clasp.dev.json`
3. Sets the active `.clasp.json` to the dev environment
4. Creates directory structure: `src/`, `tests/`, `docs/`
5. Generates starter files:
   - `.gitignore` (excludes `.clasp.json`, `node_modules/`, `.venv/`, etc.)
   - `.claspignore` (only includes `src/` and `appsscript.json`)
   - `appsscript.json` (V8 runtime, Stackdriver logging)
   - `gas_skill.toml` (default configuration)
   - `CHANGELOG.md` (Keep a Changelog format)
   - `src/Code.js` (starter function)
   - `src/Tests.js` (test harness with `runAllTests` and assertion helpers)
6. Initializes Git repo with `main` and `develop` branches
7. Pushes both branches to GitHub

**Output:**

```json
{
  "success": true,
  "project_name": "My Project",
  "prod_script_id": "1abc...xyz",
  "branches": ["main", "develop"],
  "environment": "dev"
}
```

---

### status

Show comprehensive project status.

```bash
gas-skill status
```

**Output:**

```json
{
  "branch": "feature/add-email-report",
  "environment": "dev",
  "script_id": "1abc...xyz",
  "clean_tree": true,
  "latest_commit": {"hash": "a1b2c3d"},
  "latest_tag": "v1.1.0",
  "remote_sync": {"ahead": 0, "behind": 0},
  "branches": {"local": ["main", "develop", "feature/add-email-report"]},
  "clasp_config_valid": true
}
```

**Fields explained:**

| Field | Description |
|---|---|
| `branch` | Current Git branch |
| `environment` | `prod` if on main, `dev` otherwise |
| `script_id` | Active Apps Script project ID |
| `clean_tree` | Whether there are uncommitted changes |
| `remote_sync.ahead` | Commits ahead of remote |
| `remote_sync.behind` | Commits behind remote |

---

### branch

Manage Git branches with automatic environment switching.

#### Create a feature branch

```bash
gas-skill branch create <name>
```

Creates `feature/<name>` from `develop`, sets `.clasp.json` to dev environment, and pushes the branch to GitHub.

```json
{
  "success": true,
  "branch": "feature/add-email-report",
  "from": "develop",
  "environment": "dev"
}
```

#### Switch branches

```bash
gas-skill branch switch <branch-name>
```

Switches to the specified branch. Requires a clean working tree. Automatically swaps `.clasp.json` to match the environment (prod for `main`, dev for everything else).

```json
{
  "success": true,
  "branch": "develop",
  "environment": "dev"
}
```

#### List branches

```bash
gas-skill branch list
```

Lists all local and remote branches.

```json
{
  "success": true,
  "current": "feature/add-email-report",
  "branches": ["main", "develop", "feature/add-email-report", "remotes/origin/main", "..."]
}
```

#### Delete a branch

```bash
gas-skill branch delete <branch-name>
```

Deletes the branch locally and from the remote. Only works for merged branches (safety check).

---

### commit

Create a conventional commit with automatic changelog update.

```bash
gas-skill commit -m "<description>" --type <type> [--scope <scope>]
```

| Option | Required | Description |
|---|---|---|
| `-m, --message` | Yes | Commit message description |
| `--type` | Yes | Commit type: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`, `perf` |
| `--scope` | No | Scope of the change (appears in parentheses) |

**What it does:**

1. Verifies you are NOT on `main` (direct commits to main are blocked)
2. Stages all changes (`git add -A`)
3. Creates a commit with the formatted message: `<type>(<scope>): <message>`
4. Pushes to the remote
5. Adds an entry to the `[Unreleased]` section of `CHANGELOG.md`
6. If the changelog was updated, creates a follow-up commit

**Example:**

```bash
gas-skill commit -m "add email report generator" --type feat --scope reports
# Creates commit: feat(reports): add email report generator
```

**Output:**

```json
{
  "success": true,
  "commit_hash": "a1b2c3d",
  "branch": "feature/add-email-report",
  "message": "feat(reports): add email report generator",
  "changelog_updated": true
}
```

**Commit type to changelog section mapping:**

| Type | Changelog Section |
|---|---|
| `feat` | Added |
| `fix` | Fixed |
| `refactor`, `perf`, `docs`, `chore`, `style`, `test` | Changed |

---

### push

Push local source files to the Apps Script project.

```bash
gas-skill push [--validate-only]
```

| Option | Description |
|---|---|
| `--validate-only` | Run pre-push validation without actually pushing |

**Pre-push validation checks:**

1. Not on `main` branch
2. `.clasp.json` exists
3. Script ID matches the expected environment
4. Working tree is clean (all changes committed)
5. `appsscript.json` is valid

**Output (successful push):**

```json
{
  "success": true,
  "command": "clasp push",
  "exit_code": 0,
  "stdout": "Pushed 4 files.",
  "stderr": "",
  "duration_sec": 3.2,
  "environment": "dev"
}
```

**Output (validate-only):**

```json
{
  "success": true,
  "checks": [
    {"check": "not_on_main", "passed": true, "detail": "Current branch: feature/test"},
    {"check": "clasp_config_exists", "passed": true, "detail": "/path/.clasp.json"},
    ...
  ]
}
```

---

### run

Execute a named function in the remote Apps Script project.

```bash
gas-skill run <function-name> [--params '<json>']
```

| Option | Required | Description |
|---|---|---|
| `function` | Yes | Name of the function to execute |
| `--params` | No | JSON-formatted parameters to pass to the function |

**Examples:**

```bash
# Run a function with no parameters
gas-skill run helloWorld

# Run a function with parameters
gas-skill run processData --params '{"startDate": "2026-01-01", "limit": 100}'
```

**Output:**

```json
{
  "success": true,
  "function": "processData",
  "exit_code": 0,
  "stdout": "{\"processed\": 42, \"errors\": 0}",
  "stderr": "",
  "duration_sec": 2.1
}
```

If the function fails, the output includes `error_category`:

```json
{
  "success": false,
  "function": "processData",
  "error_category": "REFERENCE",
  "stderr": "ReferenceError: getData is not defined"
}
```

---

### test-loop

Push code to Apps Script, run the test suite, and report results.

```bash
gas-skill test-loop [--max-retries N] [--delay N]
```

| Option | Default | Description |
|---|---|---|
| `--max-retries` | 5 (from config) | Maximum retry attempts (for tracking purposes) |
| `--delay` | 2 (from config) | Seconds to wait after push for log propagation |

**How it works:**

1. Auto-commits any uncommitted changes
2. Runs pre-push validation
3. Pushes code to the dev Apps Script project via `clasp push`
4. Waits for log propagation
5. Runs the test function (`runAllTests` by default) via `clasp run`
6. Parses the test output into a structured report
7. If tests pass, commits the passing state and pushes to GitHub
8. Returns the result as JSON

**Important:** The test-loop performs a **single cycle** per call. It does not retry automatically. After a failure, you fix the code, commit, and call `test-loop` again. This is by design — Claude Code drives the retry loop and applies intelligent fixes between iterations.

**Output (all tests pass):**

```json
{
  "success": true,
  "total_iterations": 1,
  "iterations": [
    {
      "iteration": 1,
      "committed": true,
      "commit_hash": "abc1234",
      "push_result": {"command": "clasp push", "success": true, "...": "..."},
      "test_report": {"total": 5, "passed": 5, "failed": 0, "errors": 0, "success": true},
      "error_category": "UNKNOWN"
    }
  ],
  "branch": "feature/my-feature",
  "final_commit": "abc1234"
}
```

**Output (tests fail):**

```json
{
  "success": false,
  "total_iterations": 1,
  "action_needed": "FIX_TEST_FAILURE",
  "error_detail": "{\"total\": 3, \"passed\": 2, \"failed\": 1, ...}",
  "branch": "feature/my-feature"
}
```

**Output (push fails):**

```json
{
  "success": false,
  "action_needed": "FIX_PUSH_ERROR",
  "error_detail": "SyntaxError: Unexpected token '}'"
}
```

**`action_needed` values:**

| Value | Meaning |
|---|---|
| `FIX_VALIDATION` | Pre-push validation failed (wrong branch, missing config, etc.) |
| `FIX_PUSH_ERROR` | `clasp push` failed (syntax error, auth issue, etc.) |
| `FIX_RUNTIME_ERROR` | `clasp run` failed (function not found, execution error) |
| `FIX_TEST_FAILURE` | Tests ran but some failed |

---

### logs

Retrieve and parse Apps Script execution logs.

```bash
gas-skill logs [--tail N] [--json]
```

| Option | Default | Description |
|---|---|---|
| `--tail` | 20 | Number of most recent log entries to return |
| `--json` | flag | Output as JSON (always enabled internally) |

**Output:**

```json
{
  "success": true,
  "entries": [
    {
      "timestamp": "2026-03-22T14:32:00Z",
      "severity": "ERROR",
      "message": "ReferenceError: x is not defined",
      "function_name": "processData",
      "stack_trace": "at processData (Code:15:3)"
    }
  ],
  "error_count": 1,
  "warning_count": 0,
  "total_entries": 1
}
```

---

### merge

Merge a source branch into a target branch with post-merge testing.

```bash
gas-skill merge --from <source-branch> --to <target-branch>
```

| Option | Required | Description |
|---|---|---|
| `--from` | Yes | Source branch to merge |
| `--to` | Yes | Target branch to merge into |

**What it does:**

1. Checks out the target branch and pulls latest
2. Merges the source branch with `--no-ff` (preserves history)
3. If merge conflicts occur, aborts and reports conflicting files
4. Pushes merged code to Apps Script (`clasp push`)
5. Runs tests on the target branch
6. If tests pass, pushes to GitHub
7. If tests fail, rolls back the merge and returns to the source branch

**Output (success):**

```json
{
  "success": true,
  "from_branch": "feature/add-email-report",
  "to_branch": "develop",
  "merge_commit": "e4f5a6b",
  "tests_passed": true,
  "pushed_to_github": true
}
```

**Output (merge conflicts):**

```json
{
  "success": false,
  "action_needed": "RESOLVE_CONFLICTS",
  "conflicting_files": ["src/Code.js", "src/Utils.js"]
}
```

**Output (post-merge tests fail):**

```json
{
  "success": false,
  "action_needed": "FIX_MERGE_TESTS",
  "test_report": {"total": 5, "passed": 3, "failed": 2, "...": "..."}
}
```

---

### release

Create a full production release with safety checks and automatic rollback.

```bash
gas-skill release --version <X.Y.Z> [--summary "<text>"]
```

| Option | Required | Description |
|---|---|---|
| `--version` | Yes | Semantic version number (e.g., `1.2.0`) |
| `--summary` | No | Release summary for the Git tag and GitHub release |

**Prerequisites:**
- Must be on the `develop` branch
- Working tree must be clean
- Tag `v<version>` must not already exist

**What it does:**

1. Merges `develop` into `main` with `--no-ff`
2. Finalizes `CHANGELOG.md` (moves `[Unreleased]` entries under the version heading)
3. Creates an annotated Git tag `v<version>`
4. Pushes to the **production** Apps Script project
5. Creates a versioned deployment (`clasp deploy`)
6. Runs smoke tests on production
7. If smoke tests pass:
   - Pushes `main` and the tag to GitHub
   - Creates a GitHub release with changelog notes
8. If smoke tests fail:
   - **Automatically rolls back**: deletes the tag, resets `main`, switches back to `develop`
   - Reports `action_needed: "FIX_PRODUCTION_SMOKE"`

**Output (success):**

```json
{
  "success": true,
  "version": "1.2.0",
  "tag": "v1.2.0",
  "deployment_id": "AKfycb...",
  "github_release_url": "https://github.com/user/repo/releases/tag/v1.2.0",
  "smoke_tests_passed": true
}
```

**Output (rollback):**

```json
{
  "success": false,
  "action_needed": "FIX_PRODUCTION_SMOKE",
  "rollback_performed": true,
  "error_detail": "Smoke tests failed"
}
```

---

### hotfix

Handle critical production bugs that can't wait for normal development.

#### Create a hotfix

```bash
gas-skill hotfix create <name>
```

Creates a `hotfix/<name>` branch from `main` (not from `develop`). Sets the environment to dev for testing.

```json
{
  "success": true,
  "branch": "hotfix/fix-quota-error",
  "from": "main",
  "environment": "dev"
}
```

#### Finish a hotfix

```bash
gas-skill hotfix finish <name> --version <X.Y.Z>
```

1. Merges the hotfix branch into `main`
2. Merges the hotfix branch into `develop` (so the fix is included in future development)
3. Pushes `develop`
4. Deletes the hotfix branch (locally and remotely)

```json
{
  "success": true,
  "version": "1.2.1",
  "tag": "v1.2.1",
  "hotfix_branch_deleted": true
}
```

---

## Branching Strategy

`gas-skill` enforces a simplified Git Flow model:

```
main ────────────────────────────────────────── (production)
  │                              ▲
  │                              │ merge --no-ff
  │                              │
  └─── develop ──────────────────┤──────────── (integration)
         │          ▲            │
         │          │ merge      │
         │          │            │
         └── feature/xxx ───────┘ ──────────── (work branches)
```

### Branch tiers

| Branch | Purpose | Pushes to GAS? | Protected? |
|---|---|---|---|
| `main` | Production-ready code | Yes (production project) | Yes |
| `develop` | Integration branch | Yes (dev project) | No |
| `feature/*` | Individual features | Yes (dev project) | No |
| `bugfix/*` | Bug fixes | Yes (dev project) | No |
| `hotfix/*` | Critical production fixes | Yes (dev project) | No |
| `experiment/*` | Experimental work | Yes (dev project) | No |

### Safety rules enforced in code

- Direct commits to `main` are **blocked** (raises `BranchProtectionError`)
- Branch switching requires a **clean working tree** (raises `DirtyTreeError`)
- `.clasp.json` is **automatically swapped** when switching branches
- Feature branches are always created from `develop`
- Hotfix branches are always created from `main`
- Merges always use `--no-ff` to preserve branch history

---

## Dual Environment Model

The project maintains two separate Apps Script projects:

| Config File | Environment | Used By |
|---|---|---|
| `.clasp.prod.json` | Production | `main` branch only |
| `.clasp.dev.json` | Development | `develop`, `feature/*`, `bugfix/*`, etc. |
| `.clasp.json` | Active (not in Git) | Whichever is currently active |

When you switch branches, `gas-skill` automatically copies the correct config to `.clasp.json`:
- Switching to `main` -> copies `.clasp.prod.json`
- Switching to any other branch -> copies `.clasp.dev.json`

This prevents accidentally pushing development code to the production project.

---

## Test Harness

The `src/Tests.js` file provides a lightweight test framework for Apps Script. Tests are JavaScript functions that follow a naming convention.

### Writing tests

Every test function must:
1. Start with `test_` in the name
2. Return an object with `{passed: boolean, message: string}`

```javascript
function test_greeting_function() {
  var result = getGreeting("Alice");
  return assertEqual(result, "Hello, Alice!", "greeting with name");
}

function test_empty_input() {
  var result = processData([]);
  return assertTrue(result.length === 0, "empty input returns empty");
}
```

### Available assertion helpers

| Function | Description |
|---|---|
| `assertEqual(actual, expected, label)` | Strict equality (`===`) |
| `assertTrue(value, label)` | Value is truthy |
| `assertFalse(value, label)` | Value is falsy |
| `assertThrows(fn, expectedMessage, label)` | Function throws an error |
| `assertDeepEqual(actual, expected, label)` | JSON.stringify equality |

### How `runAllTests` works

1. Discovers all functions starting with `test_` in the global scope
2. Calls each function inside a try/catch
3. Collects results as `PASS`, `FAIL`, or `ERROR`
4. Returns a JSON string with the complete report

The Python test-loop parses this JSON output automatically.

---

## Error Classification

When `clasp push`, `clasp run`, or tests fail, `gas-skill` classifies the error into one of these categories:

| Category | Triggers | Typical Fix |
|---|---|---|
| `AUTH` | "not logged in", 401, token expired | Run `clasp login` to re-authenticate |
| `SYNTAX` | SyntaxError, Unexpected token | Fix JavaScript syntax in source files |
| `REFERENCE` | ReferenceError, "is not defined" | Fix variable or function name |
| `TYPE` | TypeError, "is not a function" | Fix type mismatch or method call |
| `MANIFEST` | Invalid manifest, malformed JSON | Fix `appsscript.json` |
| `QUOTA` | Quota exceeded, rate limit, RESOURCE_EXHAUSTED | Wait and retry, or optimize code |
| `TIMEOUT` | Exceeded maximum execution time | Optimize code or break into batches |
| `NETWORK` | ECONNREFUSED, network errors | Retry after a delay |
| `PERMISSION` | Permission denied, 403, insufficient scope | Add required OAuth scopes to manifest |
| `NOT_FOUND` | Script not found, 404 | Check `scriptId` in `.clasp.json` |
| `UNKNOWN` | Anything else | Read the full error text |

Errors are classified using regex pattern matching. The first matching pattern wins (patterns are checked in the order listed above).

---

## Feedback Loop Architecture

The test-loop is designed around a single principle: **Claude Code is the intelligent agent; gas-skill is the reliable executor.**

```
Claude Code                              gas-skill CLI
    │                                         │
    │  1. Write/modify source files           │
    │  2. gas-skill commit ...                │
    │─────────────────────────────────────────>│
    │                                         │  commit + push to GitHub
    │<──────── JSON result ───────────────────│
    │                                         │
    │  3. gas-skill test-loop                 │
    │─────────────────────────────────────────>│
    │                                         │  push to GAS → run tests
    │<──── JSON: FAIL + error details ────────│
    │                                         │
    │  4. Read error, analyze, fix code       │
    │  5. gas-skill commit ...                │
    │─────────────────────────────────────────>│
    │<──────── JSON result ───────────────────│
    │                                         │
    │  6. gas-skill test-loop                 │
    │─────────────────────────────────────────>│
    │                                         │  push to GAS → run tests
    │<──── JSON: PASS ────────────────────────│
    │                                         │
    │  7. gas-skill merge ...                 │
    │─────────────────────────────────────────>│
```

Each test-loop call does exactly **one** push-run-evaluate cycle. This keeps Claude Code in control of the debugging process — it reads the structured error report, decides on a fix, edits files, and calls the loop again.

Every fix attempt is committed to Git, so the complete evolution of the code through the debugging process is preserved in the commit history.

---

## Changelog Management

`CHANGELOG.md` follows the [Keep a Changelog](https://keepachangelog.com/) format and is managed automatically.

### Automatic updates

- **On commit:** `gas-skill commit` adds an entry to the `[Unreleased]` section under the appropriate subsection (`Added` for feat, `Fixed` for fix, `Changed` for others)
- **On release:** `gas-skill release` moves all `[Unreleased]` entries under a new version heading with the release date

### Example changelog evolution

After `gas-skill commit -m "add email reports" --type feat`:
```markdown
## [Unreleased]

### Added
- add email reports
```

After `gas-skill commit -m "fix date parsing" --type fix`:
```markdown
## [Unreleased]

### Added
- add email reports

### Fixed
- fix date parsing
```

After `gas-skill release --version 1.1.0`:
```markdown
## [Unreleased]

## [1.1.0] - 2026-03-22
### Added
- add email reports

### Fixed
- fix date parsing
```

---

## Troubleshooting

### "Command not found: clasp"

Install clasp globally:
```bash
sudo npm install -g @google/clasp
```

### "~/.clasprc.json not found"

Authenticate clasp:
```bash
clasp login --creds /path/to/your/credentials.json
```

### "Direct commits to 'main' are not allowed"

You're on the `main` branch. Create a feature branch first:
```bash
gas-skill branch switch develop
gas-skill branch create my-feature
```

### "Working tree has uncommitted changes"

Commit your changes before switching branches:
```bash
gas-skill commit -m "save work in progress" --type chore
```

### "Missing clasp config: .clasp.dev.json"

The dev clasp config doesn't exist. Either run `gas-skill init` to set up the project, or manually create `.clasp.dev.json`:
```json
{"scriptId": "your-dev-script-id", "rootDir": "src"}
```

### AUTH errors during push or run

Your OAuth token may have expired. Re-authenticate:
```bash
clasp logout
clasp login --creds /path/to/your/credentials.json
```

### Tests pass locally but test-loop reports failure

Remember that `clasp run` executes code in the **remote** Apps Script environment, not locally. Make sure:
1. You pushed the latest code (`gas-skill push`)
2. The function `runAllTests` exists and is not renamed
3. All test functions start with `test_`

### Release fails with "smoke tests failed"

The release command automatically rolls back when smoke tests fail. Check the error detail, fix the issue on `develop`, verify with `test-loop`, and try the release again.

### Merge reports "RESOLVE_CONFLICTS"

The merge produced Git conflicts. Resolve the conflicts in the listed files, then run the merge again:
```bash
# After resolving conflicts manually
gas-skill commit -m "resolve merge conflicts" --type chore
gas-skill merge --from feature/my-feature --to develop
```
