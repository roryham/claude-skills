"""_subprocess.py — Shared subprocess execution utilities."""
import subprocess
import time
from pathlib import Path
from .models import CommandResult


def run_command(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = 120,
    env: dict | None = None,
) -> CommandResult:
    """
    Execute a command and return a structured CommandResult.

    Args:
        args:    Command and arguments as a list.
        cwd:     Working directory for the command.
        timeout: Maximum seconds to wait before killing the process.
        env:     Optional environment variables (merged with os.environ).

    Returns:
        CommandResult with stdout, stderr, exit_code, and timing.
    """
    command_str = " ".join(args)
    start = time.monotonic()

    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
            env=env,
        )
        duration = time.monotonic() - start

        return CommandResult(
            command=command_str,
            exit_code=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            success=(proc.returncode == 0),
            duration_sec=round(duration, 2),
        )

    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return CommandResult(
            command=command_str,
            exit_code=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            success=False,
            duration_sec=round(duration, 2),
        )

    except FileNotFoundError:
        duration = time.monotonic() - start
        return CommandResult(
            command=command_str,
            exit_code=-1,
            stdout="",
            stderr=f"Command not found: {args[0]}",
            success=False,
            duration_sec=round(duration, 2),
        )
