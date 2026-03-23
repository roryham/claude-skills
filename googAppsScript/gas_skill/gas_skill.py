"""gas_skill.py — Main CLI entrypoint for the gas-skill orchestrator."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import ProjectConfig
from .git_manager import GitManager
from .clasp_wrapper import ClaspWrapper
from .log_parser import classify_error, parse_test_output
from .runner import FeedbackLoopRunner
from .manifest import validate as validate_manifest, create_default as create_manifest
from .changelog import (
    create_initial as create_changelog,
    add_entry as add_changelog_entry,
    finalize_release,
    get_release_notes,
)
from .exceptions import GasSkillError


def _output(data: dict) -> None:
    """Print structured JSON output to stdout."""
    print(json.dumps(data, indent=2, default=str))


def _error(message: str, detail: str = "") -> None:
    """Print structured error JSON and exit."""
    _output({
        "success": False,
        "error": message,
        "detail": detail,
    })
    sys.exit(1)


def cmd_preflight(args: argparse.Namespace, config: ProjectConfig) -> None:
    """Validate all prerequisites."""
    from ._subprocess import run_command

    checks = []

    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append({
        "name": "python",
        "passed": sys.version_info >= (3, 11),
        "detail": py_version,
    })

    node_result = run_command(["node", "--version"])
    checks.append({
        "name": "nodejs",
        "passed": node_result.success,
        "detail": node_result.stdout or node_result.stderr,
    })

    clasp_result = run_command(["clasp", "--version"])
    checks.append({
        "name": "clasp",
        "passed": clasp_result.success,
        "detail": clasp_result.stdout or clasp_result.stderr,
    })

    git_result = run_command(["git", "--version"])
    checks.append({
        "name": "git",
        "passed": git_result.success,
        "detail": git_result.stdout or git_result.stderr,
    })

    gh_result = run_command(["gh", "auth", "status"])
    checks.append({
        "name": "gh_cli",
        "passed": gh_result.success,
        "detail": gh_result.stdout or gh_result.stderr,
    })

    clasprc = Path.home() / ".clasprc.json"
    checks.append({
        "name": "clasp_auth",
        "passed": clasprc.exists(),
        "detail": str(clasprc) if clasprc.exists() else "~/.clasprc.json not found",
    })

    config_file = config.project_root / "gas_skill.toml"
    checks.append({
        "name": "project_config",
        "passed": config_file.exists(),
        "detail": str(config_file),
    })

    manifest_path = config.project_root / "appsscript.json"
    if manifest_path.exists():
        mv = validate_manifest(manifest_path)
        checks.append({
            "name": "manifest",
            "passed": mv.ok,
            "detail": mv.message,
        })
    else:
        checks.append({
            "name": "manifest",
            "passed": False,
            "detail": "appsscript.json not found",
        })

    all_passed = all(c["passed"] for c in checks)
    _output({"all_passed": all_passed, "checks": checks})


def cmd_init(args: argparse.Namespace, config: ProjectConfig) -> None:
    """Initialize a new project."""
    clasp = ClaspWrapper(config)
    git = GitManager(config)

    import shutil

    project_root = config.project_root

    prod_result = clasp.create(args.type, args.title)
    if not prod_result.success:
        _error("Failed to create production project", prod_result.stderr)

    shutil.copy2(project_root / ".clasp.json", project_root / config.prod_config)

    dev_result = clasp.create(args.type, f"{args.title} [DEV]")
    if not dev_result.success:
        _error("Failed to create development project", dev_result.stderr)

    shutil.copy2(project_root / ".clasp.json", project_root / config.dev_config)

    for d in ["src", "tests", "docs"]:
        (project_root / d).mkdir(exist_ok=True)

    _write_gitignore(project_root)
    _write_claspignore(project_root)
    create_manifest(project_root / "appsscript.json")
    create_changelog(project_root / "CHANGELOG.md")
    _write_initial_code(project_root / "src" / "Code.js")
    _write_test_harness(project_root / "src" / "Tests.js")
    _write_gas_skill_toml(project_root, args.title)

    git._git(["init"])
    git._git(["remote", "add", "origin", args.github_url])
    git.add_all()
    git._git(["commit", "-m", "chore(init): scaffold project"])
    git._git(["branch", "-M", "main"])
    git._git(["push", "-u", "origin", "main"])
    git._git(["checkout", "-b", "develop"])
    git._git(["push", "-u", "origin", "develop"])

    _output({
        "success": True,
        "project_name": args.title,
        "prod_script_id": clasp.get_script_id(),
        "branches": ["main", "develop"],
        "environment": "dev",
    })


def cmd_branch(args: argparse.Namespace, config: ProjectConfig) -> None:
    """Branch management subcommands."""
    git = GitManager(config)

    if args.branch_action == "create":
        result = git.create_branch(
            f"{config.feature_prefix}{args.name}",
            from_branch=config.develop_branch,
        )
        _output({
            "success": result.success,
            "branch": f"{config.feature_prefix}{args.name}",
            "from": config.develop_branch,
            "environment": "dev",
        })

    elif args.branch_action == "switch":
        result = git.checkout(args.name)
        env = "prod" if args.name == config.main_branch else "dev"
        _output({
            "success": result.success,
            "branch": args.name,
            "environment": env,
        })

    elif args.branch_action == "list":
        branches = git.list_branches(remote=True)
        current = git.current_branch()
        _output({
            "success": True,
            "current": current,
            "branches": branches,
        })

    elif args.branch_action == "delete":
        result = git.delete_branch(args.name)
        _output({
            "success": result.success,
            "deleted": args.name,
        })


def cmd_commit(args: argparse.Namespace, config: ProjectConfig) -> None:
    """Create a conventional commit."""
    git = GitManager(config)

    scope_part = f"({args.scope})" if args.scope else ""
    message = f"{args.type}{scope_part}: {args.message}"

    git.add_all()
    result = git.commit(message)

    if not result.success:
        _error("Commit failed", result.stderr)

    git.push()
    commit_hash = git.head_hash()

    changelog_path = config.project_root / "CHANGELOG.md"
    add_changelog_entry(changelog_path, args.type, args.message)

    if not git.is_clean():
        git.add_all()
        git._git(["commit", "-m", "docs(changelog): update unreleased"])
        git.push()

    _output({
        "success": True,
        "commit_hash": commit_hash,
        "branch": git.current_branch(),
        "message": message,
        "changelog_updated": True,
    })


def cmd_push(args: argparse.Namespace, config: ProjectConfig) -> None:
    """Push to Apps Script."""
    clasp = ClaspWrapper(config)

    if hasattr(args, "validate_only") and args.validate_only:
        runner = FeedbackLoopRunner(config)
        checks = runner._validate_pre_push()
        all_ok = all(c["passed"] for c in checks)
        _output({"success": all_ok, "checks": checks})
        return

    result = clasp.push()
    _output({
        "success": result.success,
        "command": result.command,
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "duration_sec": result.duration_sec,
        "environment": "prod" if GitManager(config).current_branch() == config.main_branch else "dev",
    })


def cmd_run(args: argparse.Namespace, config: ProjectConfig) -> None:
    """Execute a remote function."""
    clasp = ClaspWrapper(config)
    result = clasp.run(args.function, params=args.params if hasattr(args, "params") else None)

    response = {
        "success": result.success,
        "function": args.function,
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "duration_sec": result.duration_sec,
    }

    if not result.success:
        response["error_category"] = classify_error(result.stderr).value

    _output(response)


def cmd_test_loop(args: argparse.Namespace, config: ProjectConfig) -> None:
    """Run the feedback loop."""
    runner = FeedbackLoopRunner(config)
    max_retries = args.max_retries if hasattr(args, "max_retries") and args.max_retries else config.max_retries
    delay = args.delay if hasattr(args, "delay") and args.delay else config.retry_delay_sec

    report = runner.run(max_retries=max_retries, delay=delay)
    _output(json.loads(report.to_json()))


def cmd_logs(args: argparse.Namespace, config: ProjectConfig) -> None:
    """Retrieve and parse logs."""
    clasp = ClaspWrapper(config)
    result = clasp.logs(json_output=True)

    if not result.success:
        _error("Failed to retrieve logs", result.stderr)

    from .log_parser import parse_log_entries
    entries = parse_log_entries(result.stdout)

    tail = args.tail if hasattr(args, "tail") else 20
    entries = entries[-tail:]

    _output({
        "success": True,
        "entries": [
            {
                "timestamp": e.timestamp,
                "severity": e.severity.value,
                "message": e.message,
                "function_name": e.function_name,
                "stack_trace": e.stack_trace,
            }
            for e in entries
        ],
        "error_count": sum(1 for e in entries if e.severity.value == "ERROR"),
        "warning_count": sum(1 for e in entries if e.severity.value == "WARNING"),
        "total_entries": len(entries),
    })


def cmd_merge(args: argparse.Namespace, config: ProjectConfig) -> None:
    """Merge branches."""
    git = GitManager(config)
    clasp = ClaspWrapper(config)

    merge_msg = f"merge({args.to}): integrate {args.from_branch}"

    try:
        result = git.merge(args.from_branch, args.to, merge_msg)
    except Exception as e:
        _error("Merge failed", str(e))
        return

    if not result.success:
        if "CONFLICT" in result.stdout or "CONFLICT" in result.stderr:
            conflict_result = git._git(["diff", "--name-only", "--diff-filter=U"])
            conflicting = conflict_result.stdout.strip().splitlines()
            git.abort_merge()
            _output({
                "success": False,
                "action_needed": "RESOLVE_CONFLICTS",
                "conflicting_files": conflicting,
            })
            return
        _error("Merge failed", result.stderr)
        return

    push_result = clasp.push()
    if not push_result.success:
        git.reset_hard("HEAD~1")
        git.checkout(args.from_branch)
        _error("Push failed after merge", push_result.stderr)
        return

    import time
    time.sleep(config.log_wait_sec)

    run_result = clasp.run(config.test_runner_function)
    if run_result.success:
        test_report = parse_test_output(run_result.stdout)
        if test_report.success:
            git.push(args.to)
            _output({
                "success": True,
                "from_branch": args.from_branch,
                "to_branch": args.to,
                "merge_commit": git.head_hash(),
                "tests_passed": True,
                "pushed_to_github": True,
            })
            return
        else:
            git.reset_hard("HEAD~1")
            git.checkout(args.from_branch)
            _output({
                "success": False,
                "action_needed": "FIX_MERGE_TESTS",
                "test_report": json.loads(test_report.to_json()),
            })
            return

    git.reset_hard("HEAD~1")
    git.checkout(args.from_branch)
    _error("Test execution failed after merge", run_result.stderr)


def cmd_release(args: argparse.Namespace, config: ProjectConfig) -> None:
    """Create a production release."""
    git = GitManager(config)
    clasp = ClaspWrapper(config)

    import shutil

    version = args.version
    summary = args.summary if hasattr(args, "summary") and args.summary else f"Release v{version}"
    tag_name = f"v{version}"

    current = git.current_branch()
    if current != config.develop_branch:
        _error(f"Must be on '{config.develop_branch}' to start a release, currently on '{current}'")

    if not git.is_clean():
        _error("Working tree is not clean")

    existing_tag = git._git(["tag", "-l", tag_name])
    if existing_tag.stdout.strip():
        _error(f"Tag '{tag_name}' already exists")

    merge_msg = f"release(main): v{version} - {summary}"
    merge_result = git.merge(config.develop_branch, config.main_branch, merge_msg)
    if not merge_result.success:
        _error("Merge to main failed", merge_result.stderr)

    changelog_path = config.project_root / "CHANGELOG.md"
    finalize_release(changelog_path, version)
    git.add_all()
    git._git(["commit", "-m", f"docs(changelog): finalize v{version}"])

    git.tag(tag_name, f"Release {tag_name}: {summary}")

    push_result = clasp.push()
    if not push_result.success:
        git._git(["tag", "-d", tag_name])
        git.reset_hard("HEAD~2")
        shutil.copy2(config.project_root / config.dev_config, config.project_root / ".clasp.json")
        git.checkout(config.develop_branch)
        _error("Push to production failed", push_result.stderr)

    deploy_result = clasp.deploy(description=tag_name)

    import time
    time.sleep(config.log_wait_sec)

    run_result = clasp.run(config.test_runner_function)
    if run_result.success:
        test_report = parse_test_output(run_result.stdout)
        if test_report.success:
            git.push(config.main_branch)
            git.push_tag(tag_name)

            notes = get_release_notes(changelog_path, version)
            notes_file = config.project_root / ".release_notes_tmp.md"
            notes_file.write_text(notes)
            gh_result = git.gh_create_release(tag_name, tag_name, str(notes_file))
            notes_file.unlink(missing_ok=True)

            _output({
                "success": True,
                "version": version,
                "tag": tag_name,
                "deployment_id": deploy_result.stdout if deploy_result.success else "unknown",
                "github_release_url": gh_result.stdout.strip() if gh_result.success else "",
                "smoke_tests_passed": True,
            })
            return

    git._git(["tag", "-d", tag_name])
    git.reset_hard("HEAD~2")
    shutil.copy2(config.project_root / config.dev_config, config.project_root / ".clasp.json")
    git.checkout(config.develop_branch)
    _output({
        "success": False,
        "action_needed": "FIX_PRODUCTION_SMOKE",
        "rollback_performed": True,
        "error_detail": run_result.stderr if not run_result.success else "Smoke tests failed",
    })


def cmd_status(args: argparse.Namespace, config: ProjectConfig) -> None:
    """Show project status."""
    git = GitManager(config)
    clasp = ClaspWrapper(config)

    branch = git.current_branch()
    env = "prod" if branch == config.main_branch else "dev"

    status_data = {
        "branch": branch,
        "environment": env,
        "script_id": clasp.get_script_id() or "unknown",
        "clean_tree": git.is_clean(),
        "latest_commit": {
            "hash": git.head_hash(),
        },
        "latest_tag": git.latest_tag(),
        "remote_sync": git.remote_sync_status(),
        "branches": {
            "local": git.list_branches(remote=False),
        },
        "clasp_config_valid": (config.project_root / ".clasp.json").exists(),
    }

    _output(status_data)


def cmd_hotfix(args: argparse.Namespace, config: ProjectConfig) -> None:
    """Hotfix management."""
    git = GitManager(config)

    if args.hotfix_action == "create":
        branch_name = f"{config.hotfix_prefix}{args.name}"
        result = git.create_branch(branch_name, from_branch=config.main_branch)
        _output({
            "success": result.success,
            "branch": branch_name,
            "from": config.main_branch,
            "environment": "dev",
        })

    elif args.hotfix_action == "finish":
        branch_name = f"{config.hotfix_prefix}{args.name}"
        version = args.version
        tag_name = f"v{version}"

        merge_msg = f"hotfix(main): v{version} - {args.name}"
        git.merge(branch_name, config.main_branch, merge_msg)

        git.merge(branch_name, config.develop_branch,
                  f"hotfix(develop): merge {branch_name}")
        git.push(config.develop_branch)

        git.checkout(config.develop_branch)
        git.delete_branch(branch_name, remote=True)

        _output({
            "success": True,
            "version": version,
            "tag": tag_name,
            "hotfix_branch_deleted": True,
        })


# ── File generation helpers ────────────────────────────────────

def _write_gitignore(project_root: Path) -> None:
    content = """\
# Environment
.venv/
__pycache__/
*.pyc
.mypy_cache/
.ruff_cache/
.pytest_cache/

# clasp active config (environment-specific)
.clasp.json

# Node
node_modules/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Temporary
*.tmp
.release_notes_tmp.md
"""
    (project_root / ".gitignore").write_text(content)


def _write_claspignore(project_root: Path) -> None:
    content = """\
# Ignore everything except src/ and appsscript.json
**/**
!src/**
!appsscript.json
"""
    (project_root / ".claspignore").write_text(content)


def _write_initial_code(filepath: Path) -> None:
    content = """\
/**
 * Code.js — Main application logic.
 *
 * This file is the entry point for the Apps Script project.
 */

/**
 * Example function.
 * @returns {string} A greeting message.
 */
function helloWorld() {
  return "Hello from Apps Script!";
}
"""
    filepath.write_text(content)


def _write_test_harness(filepath: Path) -> None:
    content = """\
/**
 * Tests.js — Lightweight test harness for Apps Script.
 *
 * Convention:
 *   - All test functions start with "test_"
 *   - Each test function returns {passed: bool, message: string}
 *   - runAllTests() discovers and runs all test_ functions
 *   - Results are returned as JSON for parsing by the Python orchestrator
 */

function runAllTests() {
  var results = [];
  var totalPassed = 0;
  var totalFailed = 0;
  var totalErrors = 0;

  var globalThis_ = this;
  var testFunctions = Object.keys(globalThis_).filter(function(name) {
    return name.indexOf("test_") === 0 && typeof globalThis_[name] === "function";
  });

  testFunctions.forEach(function(funcName) {
    var result = {
      function: funcName,
      status: "ERROR",
      message: "",
      timestamp: new Date().toISOString(),
      stack: ""
    };

    try {
      var outcome = globalThis_[funcName]();
      if (outcome && outcome.passed === true) {
        result.status = "PASS";
        result.message = outcome.message || "OK";
        totalPassed++;
      } else {
        result.status = "FAIL";
        result.message = (outcome && outcome.message) ? outcome.message : "Test returned falsy or missing .passed";
        totalFailed++;
      }
    } catch (e) {
      result.status = "ERROR";
      result.message = e.message || String(e);
      result.stack = e.stack || "";
      totalErrors++;
    }

    results.push(result);
  });

  var report = {
    total: results.length,
    passed: totalPassed,
    failed: totalFailed,
    errors: totalErrors,
    success: (totalFailed === 0 && totalErrors === 0 && results.length > 0),
    details: results
  };

  return JSON.stringify(report);
}

function assertEqual(actual, expected, label) {
  var prefix = label ? label + ": " : "";
  if (actual === expected) {
    return { passed: true, message: prefix + "OK" };
  }
  return {
    passed: false,
    message: prefix + "Expected " + JSON.stringify(expected) +
             " but got " + JSON.stringify(actual)
  };
}

function assertTrue(value, label) {
  var prefix = label ? label + ": " : "";
  if (value) {
    return { passed: true, message: prefix + "OK" };
  }
  return { passed: false, message: prefix + "Expected truthy, got " + JSON.stringify(value) };
}

function test_example_pass() {
  return assertEqual(1 + 1, 2, "basic arithmetic");
}

function test_example_string() {
  var result = "hello" + " " + "world";
  return assertEqual(result, "hello world", "string concatenation");
}
"""
    filepath.write_text(content)


def _write_gas_skill_toml(project_root: Path, project_name: str) -> None:
    content = f"""\
[project]
name = "{project_name.lower().replace(' ', '-')}"
description = ""

[clasp]
root_dir = "src"
prod_config = ".clasp.prod.json"
dev_config = ".clasp.dev.json"

[test_loop]
max_retries = 5
retry_delay_sec = 2
log_wait_sec = 3
test_runner_function = "runAllTests"

[git]
remote = "origin"
main_branch = "main"
develop_branch = "develop"
feature_prefix = "feature/"
bugfix_prefix = "bugfix/"
hotfix_prefix = "hotfix/"
experiment_prefix = "experiment/"

[logging]
level = "INFO"
format = "json"
"""
    (project_root / "gas_skill.toml").write_text(content)


# ── Argument parser ────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="gas-skill",
        description="Claude Code skill for Google Apps Script integration",
    )
    parser.add_argument(
        "--project-root", type=Path, default=None,
        help="Project root directory (default: current directory)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("preflight", help="Validate prerequisites")

    init_parser = subparsers.add_parser("init", help="Initialize project")
    init_parser.add_argument("--type", required=True,
                             choices=["sheets", "docs", "slides", "forms", "webapp", "api"],
                             help="Apps Script project type")
    init_parser.add_argument("--title", required=True, help="Project title")
    init_parser.add_argument("--github-url", required=True, help="GitHub remote URL")

    branch_parser = subparsers.add_parser("branch", help="Branch management")
    branch_sub = branch_parser.add_subparsers(dest="branch_action", required=True)
    branch_create = branch_sub.add_parser("create", help="Create feature branch")
    branch_create.add_argument("name", help="Branch name (without prefix)")
    branch_switch = branch_sub.add_parser("switch", help="Switch branch")
    branch_switch.add_argument("name", help="Branch name")
    branch_sub.add_parser("list", help="List branches")
    branch_delete = branch_sub.add_parser("delete", help="Delete branch")
    branch_delete.add_argument("name", help="Branch name")

    commit_parser = subparsers.add_parser("commit", help="Create conventional commit")
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")
    commit_parser.add_argument("--type", required=True,
                               choices=["feat", "fix", "refactor", "test",
                                        "docs", "chore", "style", "perf"],
                               help="Commit type")
    commit_parser.add_argument("--scope", default="", help="Commit scope")

    push_parser = subparsers.add_parser("push", help="Push to Apps Script")
    push_parser.add_argument("--validate-only", action="store_true",
                             help="Only validate, don't push")

    run_parser = subparsers.add_parser("run", help="Execute remote function")
    run_parser.add_argument("function", help="Function name to execute")
    run_parser.add_argument("--params", default=None, help="JSON parameters")

    test_loop_parser = subparsers.add_parser("test-loop", help="Run feedback loop")
    test_loop_parser.add_argument("--max-retries", type=int, default=None,
                                  help="Maximum retry attempts")
    test_loop_parser.add_argument("--delay", type=int, default=None,
                                  help="Delay between retries in seconds")

    logs_parser = subparsers.add_parser("logs", help="Retrieve logs")
    logs_parser.add_argument("--json", action="store_true", dest="json_output",
                             help="Output as JSON")
    logs_parser.add_argument("--tail", type=int, default=20,
                             help="Number of log entries to show")

    merge_parser = subparsers.add_parser("merge", help="Merge branches")
    merge_parser.add_argument("--from", dest="from_branch", required=True,
                              help="Source branch")
    merge_parser.add_argument("--to", required=True, help="Target branch")

    release_parser = subparsers.add_parser("release", help="Create production release")
    release_parser.add_argument("--version", required=True, help="Semantic version (X.Y.Z)")
    release_parser.add_argument("--summary", default="", help="Release summary")

    hotfix_parser = subparsers.add_parser("hotfix", help="Hotfix management")
    hotfix_sub = hotfix_parser.add_subparsers(dest="hotfix_action", required=True)
    hotfix_create = hotfix_sub.add_parser("create", help="Create hotfix branch")
    hotfix_create.add_argument("name", help="Hotfix name")
    hotfix_finish = hotfix_sub.add_parser("finish", help="Finish hotfix")
    hotfix_finish.add_argument("name", help="Hotfix name")
    hotfix_finish.add_argument("--version", required=True, help="Patch version (X.Y.Z)")

    subparsers.add_parser("status", help="Show project status")

    return parser


# ── Command dispatch ────────────────────────────────────────────

COMMAND_MAP = {
    "preflight": cmd_preflight,
    "init": cmd_init,
    "branch": cmd_branch,
    "commit": cmd_commit,
    "push": cmd_push,
    "run": cmd_run,
    "test-loop": cmd_test_loop,
    "logs": cmd_logs,
    "merge": cmd_merge,
    "release": cmd_release,
    "status": cmd_status,
    "hotfix": cmd_hotfix,
}


def main() -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    project_root = args.project_root or Path.cwd()
    config = ProjectConfig.load(project_root)

    command_fn = COMMAND_MAP.get(args.command)
    if command_fn is None:
        _error(f"Unknown command: {args.command}")
        return

    try:
        command_fn(args, config)
    except GasSkillError as e:
        _error(type(e).__name__, str(e))
    except Exception as e:
        _error("UnexpectedError", str(e))


if __name__ == "__main__":
    main()
