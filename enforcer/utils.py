import os
import subprocess
import threading
from multiprocessing import Queue
from typing import List, Optional


def get_git_root(
    cwd: Optional[str] = None, timeout: Optional[int] = None
) -> Optional[str]:
    """
    Returns the absolute path to the git repository root, or None if not in a git repo.
    """
    try:
        result = run_command(
            ["git", "rev-parse", "--show-toplevel"],
            return_output=True,
            check=True,
            cwd=cwd,
            timeout=timeout,
        )
        return result.stdout.strip()
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return None


def get_git_modified_files(
    cwd: Optional[str] = None, timeout: Optional[int] = None
) -> List[str]:
    """
    Returns a list of files modified in the current git repository.
    """
    try:
        run_command(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            return_output=True,
            cwd=cwd,
            timeout=timeout,
        )

        # Get the list of modified files
        result = run_command(
            ["git", "status", "--porcelain"],
            check=True,
            return_output=True,
            cwd=cwd,
            timeout=timeout,
        )

        modified_files = []
        for line in result.stdout.splitlines():
            if line:
                status = line[0:2]
                # Only include modified, added, untracked. Not deleted.
                if status in (" M", "M ", "A ", "??"):
                    file_path = line[3:].strip()
                    # Handle paths with spaces that might be quoted
                    if file_path.startswith('"') and file_path.endswith('"'):
                        file_path = file_path[1:-1]
                    modified_files.append(file_path)
        return modified_files
    except subprocess.CalledProcessError as e:
        # If the error indicates it's not a git repo, that's a valid state.
        if "not a git repository" in (e.stderr or "").lower():
            print("Warning: Not a git repository.")
            return []
        # Otherwise, it's an unexpected error that should be reported.
        raise e
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        # Let the caller handle these critical errors.
        raise e


def run_command(
    command: List[str],
    return_output: bool = False,
    check: bool = False,
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    log_queue: Optional[Queue] = None,
) -> subprocess.CompletedProcess:
    """
    ! A more robust command runner that handles large outputs and potential hangs.
    It uses a timeout to prevent indefinite hangs and Popen with communicate
    to avoid pipe deadlocks, and supports real-time logging via a queue.
    """
    # * The subprocess lock can cause deadlocks if a process hangs while
    # holding it. We'll remove it as Popen is thread-safe.
    # with subprocess_lock:
    cmd_str = " ".join(command)
    if log_queue:
        log_queue.put(f"Running command: {cmd_str}")

    try:
        # * Use Popen and communicate to avoid deadlocks from full pipes.
        # * Use DEVNULL for stdin to prevent processes from hanging while waiting for input.
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            encoding="utf-8",
            errors="ignore",
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout)
            if log_queue:
                log_queue.put(
                    f"Command finished with code {process.returncode}: {cmd_str}"
                )
        except subprocess.TimeoutExpired as e:
            if log_queue:
                log_queue.put(f"Command timed out after {timeout}s: {cmd_str}")
            process.kill()
            # Try to get output after killing
            stdout, stderr = process.communicate()
            # Re-create the exception with the output we managed to get
            raise subprocess.TimeoutExpired(
                cmd=e.cmd, timeout=e.timeout, output=stdout, stderr=stderr
            ) from e

        if check and process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, command, output=stdout, stderr=stderr
            )

        # If not returning output, don't include it in the result
        if not return_output:
            stdout, stderr = "", ""

        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)

    except FileNotFoundError as e:
        if log_queue:
            log_queue.put(f"Command not found: {command[0]}")
        # Re-raise with a more informative message
        raise FileNotFoundError(f"Command not found: {command[0]}") from e
    except subprocess.CalledProcessError as e:
        if log_queue:
            log_queue.put(f"Command failed with code {e.returncode}: {cmd_str}")
        # This is raised when check=True and the command fails
        # Re-raise the exception so the caller can handle it.
        raise e
