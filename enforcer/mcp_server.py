import gc
import json
import multiprocessing as mp
import queue
from concurrent.futures import TimeoutError
from typing import List, Optional

from fastmcp import FastMCP

from .api import run_enforcer_as_string
from .utils import get_git_modified_files

mcp = FastMCP("agent_enforcer")


def _run_check_process(
    targets: Optional[str],
    check_git_modified_files: bool,
    verbose: bool,
    result_queue: mp.Queue,
    log_queue: Optional[mp.Queue] = None,
):
    """Wraps the core logic to be run in a separate process."""
    gc.disable()  # ! Disable GC to prevent potential deadlocks in subprocesses.

    try:
        paths_to_check = None
        if log_queue:
            log_queue.put("Analyzing run parameters...")

        if check_git_modified_files:
            if log_queue:
                log_queue.put("Checking for modified git files...")
            paths_to_check = get_git_modified_files()
            if not paths_to_check:
                result_queue.put(
                    ("success", "No modified files found in git status to check.")
                )
                return
        elif targets:
            if log_queue:
                log_queue.put(f"Received targets for analysis: {targets}")
            try:
                parsed_targets = json.loads(targets)
                if isinstance(parsed_targets, list):
                    paths_to_check = parsed_targets
                else:
                    paths_to_check = [str(parsed_targets)]
            except json.JSONDecodeError:
                paths_to_check = [targets]

        if log_queue:
            log_queue.put(f"Starting analysis on paths: {paths_to_check}")

        # Note: run_enforcer_as_string now expects log_queue, not log_collector
        result = run_enforcer_as_string(
            paths=paths_to_check,
            root_path=".",
            verbose=verbose,
            log_queue=log_queue,
        )

        if log_queue:
            log_queue.put("Analysis finished successfully.")
        result_queue.put(("success", result))
    except Exception as e:
        if log_queue:
            log_queue.put(f"[CRITICAL] Unhandled exception in worker process: {e}")
        result_queue.put(("error", str(e)))
    finally:
        gc.enable()  # * Re-enable GC.


@mcp.tool()
def run_check(
    targets: Optional[str] = None,
    check_git_modified_files: bool = False,
    verbose: bool = False,
    timeout_seconds: int = 45,
    debug: bool = False,
) -> str:
    """
    Runs a quality check with a timeout in a separate process to prevent hangs.

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
    # Use multiprocessing to avoid hangs from subprocesses in threads on Windows.
    result_queue = mp.Queue()
    log_queue = mp.Queue() if debug else None

    process = mp.Process(
        target=_run_check_process,
        args=(targets, check_git_modified_files, verbose, result_queue, log_queue),
    )
    process.start()
    process.join(timeout=timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join(timeout=1)  # Allow time for termination
        error_message = (
            f"Error: The quality check timed out after {timeout_seconds} seconds."
        )
        if debug and log_queue is not None:
            log_messages = []
            while not log_queue.empty():
                try:
                    log_messages.append(log_queue.get_nowait())
                except queue.Empty:
                    break
            if log_messages:
                log_str = "\n".join(log_messages)
                error_message += f"\n\n--- Captured Log ---\n{log_str}"
            else:
                error_message += "\n\n--- Captured Log ---\n(No logs were captured or process was terminated abruptly)"
        return error_message

    try:
        status, result = result_queue.get_nowait()
        if status == "error":
            return f"Error during check: {result}"
        return result
    except queue.Empty:
        return "Error: Worker process finished but returned no result."


def main():
    mcp.run()


if __name__ == "__main__":
    main()
