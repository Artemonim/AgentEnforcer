import gc
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import List, Optional

from fastmcp import FastMCP

from .api import run_enforcer_as_string
from .utils import get_git_modified_files

mcp = FastMCP("agent_enforcer")


def _run_check_sync(
    targets: Optional[str],
    check_git_modified_files: bool,
    verbose: bool,
    log_collector: Optional[List[str]] = None,
) -> str:
    """Synchronous wrapper for the core logic that will be run in a thread."""
    gc.disable()  # ! Disable GC to prevent potential deadlocks in subprocesses from threads.
    try:
        paths_to_check = None

        if check_git_modified_files:
            paths_to_check = get_git_modified_files()
            if not paths_to_check:
                return "No modified files found in git status to check."
        elif targets:
            try:
                parsed_targets = json.loads(targets)
                if isinstance(parsed_targets, list):
                    paths_to_check = parsed_targets
                else:
                    paths_to_check = [str(parsed_targets)]
            except json.JSONDecodeError:
                paths_to_check = [targets]

        return run_enforcer_as_string(
            paths=paths_to_check,
            root_path=".",
            verbose=verbose,
            log_collector=log_collector,
        )
    finally:
        gc.enable()  # * Re-enable GC after the check is complete.


@mcp.tool()
def run_check(
    targets: Optional[str] = None,
    check_git_modified_files: bool = False,
    verbose: bool = False,
    timeout_seconds: int = 45,
    debug: bool = False,
) -> str:
    f"""
    Runs a quality check with a {timeout_seconds}-second timeout.

    The tool can be run in one of three modes:
    1. Git Modified: Set 'check_git_modified_files' to True to check files reported as modified by git.
    2. Specific Targets: Provide a JSON string array of file or directory paths in 'targets'.
    3. Full Project: If neither of the above is provided, it checks the entire project directory.

    :param targets: A JSON string representing a list of relative paths (e.g., '["src/main.py", "tests/"]').
    :param check_git_modified_files: If True, ignores 'targets' and checks files modified in git.
    :param verbose: If True, provides a detailed, file-by-file list of all issues.
    :param timeout_seconds: The timeout for the check in seconds.
    :param debug: If True, enables debug mode, which will return the full log on timeout.
    :return: A string containing the formatted results or an error message if it times out.
    """
    log_messages: List[str] = []
    log_collector = log_messages if debug else None

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        _run_check_sync, targets, check_git_modified_files, verbose, log_collector
    )

    try:
        # Get the result from the future, with a timeout.
        return future.result(timeout=timeout_seconds)
    except TimeoutError:
        error_message = (
            f"Error: The quality check timed out after {timeout_seconds} seconds."
        )
        if debug:
            log_str = "\n".join(log_messages)
            error_message += f"\n\n--- Captured Log ---\n{log_str}"
        return error_message
    finally:
        # Ensure the executor is always shut down.
        executor.shutdown(wait=False)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
