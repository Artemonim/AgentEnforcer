import json
import os
import subprocess
import sys
import traceback
from typing import Optional

from fastmcp import FastMCP

from .utils import get_git_modified_files

mcp: FastMCP = FastMCP("agent_enforcer")


def _run_check_impl(
    targets: Optional[str] = None,
    check_git_modified_files: bool = False,
    verbose: bool = False,
    timeout_seconds: int = 0,
    debug: bool = False,
    root: Optional[str] = None,
) -> str:
    """
    Runs a quality check by executing the enforcer CLI as a separate process.
    This ensures that any long-running linters or formatters can be reliably
    timed out and terminated.
    """
    # --- Root Path Management ---
    if not root:
        root = os.getcwd()

    if not os.path.isdir(root):
        return f"Error: The provided root path is not a valid directory: {root}"

    # --- Command and Timeout Configuration ---
    timeout = timeout_seconds if timeout_seconds > 0 else None
    command = [sys.executable, "-m", "enforcer.main"]

    if verbose:
        command.append("--verbose")

    try:
        # --- Determine Target Files ---
        parsed_targets = None
        if check_git_modified_files:
            # Pass timeout to git call as a safeguard, though the global
            # timeout on the main process is the primary controller.
            git_timeout = 15 if not timeout or timeout > 15 else timeout
            parsed_targets = get_git_modified_files(timeout=git_timeout)
            if not parsed_targets:
                return "! No modified files to check."
        elif targets:
            if targets.lower() not in ("null", "[]", '""'):
                try:
                    parsed_targets = json.loads(targets)
                    if not isinstance(parsed_targets, list):
                        parsed_targets = [str(parsed_targets)]
                except json.JSONDecodeError:
                    return "Error: Invalid JSON format for targets."

        if parsed_targets:
            command.extend(parsed_targets)

        # --- Execute the Enforcer Process ---
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=root,
            timeout=timeout,
            encoding="utf-8",
            errors="ignore",
        )

        if result.returncode != 0 and result.stderr:
            return f"Enforcer process failed:\n--- STDERR ---\n{result.stderr}\n--- STDOUT ---\n{result.stdout}"

        return result.stdout

    except subprocess.TimeoutExpired as e:
        cmd_str = " ".join(command)
        stdout = e.stdout or ""
        stderr = e.stderr or ""
        stdout_str = (
            stdout if isinstance(stdout, str) else stdout.decode("utf-8", "ignore")
        )
        stderr_str = (
            stderr if isinstance(stderr, str) else stderr.decode("utf-8", "ignore")
        )

        # Build a detailed trace
        trace = (
            f"Error: Main enforcer process timed out after {timeout_seconds}s.\n"
            f"Command: {cmd_str}\n"
            f"Working Directory: {root}\n"
        )
        if debug:
            trace += f"--- Captured STDOUT ---\n{stdout_str}\n"
            trace += f"--- Captured STDERR ---\n{stderr_str}\n"
        else:
            trace += "(Run with 'debug: true' for full stdout/stderr dump)"

        return trace

    except Exception:
        return (
            f"An unexpected error occurred in the MCP server:\n{traceback.format_exc()}"
        )


run_check = mcp.tool()(_run_check_impl)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
