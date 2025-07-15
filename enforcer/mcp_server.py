import json
import os
import subprocess
import sys
# Add time to imports
import time
import traceback
from typing import List, Optional

from fastmcp import FastMCP

from .config import load_config
from .core import Enforcer
from .utils import get_git_modified_files, run_command

mcp: FastMCP = FastMCP("agent_enforcer")


@mcp.tool()
def run_check(
    targets: Optional[str] = None,
    check_git_modified_files: bool = False,
    verbose: bool = False,
    timeout_seconds: int = 0,
    debug: bool = False,
    root: Optional[str] = None,
) -> str:
    """
    Runs a quality check by calling the Agent Enforcer core logic directly.

    This tool acts as a simple wrapper, ensuring that the core logic runs in a
    separate, clean process, which is more stable, especially on Windows.

    :param targets: A JSON string representing a list of file or directory paths.
        If omitted, the entire repository is checked.
    :param check_git_modified_files: If True, ignores 'targets' and checks files
        modified in git. Default: false.
    :param verbose: If True, provides a detailed, file-by-file list of all issues.
        Default: false.
    :param timeout_seconds: The timeout for the check in seconds. Set to 0 to
        disable the timeout. Default: 0.
    :param debug: If True, returns the full stdout of the tool on timeout for
        debugging. This is only useful for diagnosing hangs. Default: false.
    :param root: Optional root directory for the check. If provided, the CLI
        will run relative to this path.
    :return: A string containing the formatted results or an error message.
    """
    # --- Root Path Management ---
    # If root is not provided, default to the current working directory.
    # This assumes the IDE/caller sets the CWD to the project root.
    if not root:
        root = os.getcwd()

    if not os.path.isdir(root):
        return f"Error: The provided root path is not a valid directory: {root}"

    # Change CWD to the project root for the duration of the check.
    # This is critical for git commands and relative paths to work correctly.
    original_cwd = os.getcwd()
    os.chdir(root)

    # --- Centralized Timeout Management ---
    timeout = timeout_seconds if timeout_seconds > 0 else None

    try:
        # --- Determine Target Files ---
        parsed_targets = None
        if check_git_modified_files:
            parsed_targets = get_git_modified_files(timeout=timeout)
            if not parsed_targets:
                return "! No modified files to check."
        elif targets:
            # * Handle "null" or empty list strings from client
            if targets.lower() in ("null", "[]", '""'):
                targets = None

            if targets:
                try:
                    parsed_targets = json.loads(targets)
                    if not isinstance(parsed_targets, list):
                        parsed_targets = [str(parsed_targets)]
                except json.JSONDecodeError:
                    return "Error: Invalid JSON format for targets."

        # --- Run the Enforcer ---
        config = load_config(root)
        enforcer = Enforcer(
            root_path=root,
            target_paths=parsed_targets,
            config=config,
            verbose=verbose,
            timeout=timeout,
        )

        result_output = enforcer.run_checks()
        return result_output

    except subprocess.TimeoutExpired as e:
        cmd_str = " ".join(e.cmd) if isinstance(e.cmd, list) else str(e.cmd)
        if debug and hasattr(e, "output") and e.output:
            output = (
                e.output.decode("utf-8", "ignore")
                if isinstance(e.output, bytes)
                else e.output
            )
            stderr = (
                e.stderr.decode("utf-8", "ignore")
                if isinstance(e.stderr, bytes)
                else e.stderr
            )
            return f"Tool timed out after {timeout_seconds}s while running: {cmd_str}\n\n--- Captured Output ---\n{output}\n{stderr}"
        else:
            return f"Error: Tool timed out after {timeout_seconds}s while running command: {cmd_str}"

    except Exception as e:
        return f"An unexpected error occurred: {e}\n{traceback.format_exc()}"

    finally:
        # Restore the original working directory
        os.chdir(original_cwd)


test = "test"


def main():
    mcp.run()


if __name__ == "__main__":
    main()
