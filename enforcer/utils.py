import os
import subprocess
import threading
from multiprocessing import Queue
from typing import List, Optional

subprocess_lock = threading.Lock()


def get_git_modified_files() -> List[str]:
    """
    Returns a list of files modified in the current git repository.
    """
    try:
        # Ensure git is installed and we are in a repo
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
        )

        # Get the list of modified files
        result = subprocess.run(
            ["git", "status", "--porcelain"], check=True, capture_output=True, text=True
        )

        modified_files = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                # The file path is the second part of the line
                parts = line.strip().split(maxsplit=1)
                if len(parts) > 1:
                    modified_files.append(parts[1])
        return modified_files
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        if "Not a git repository" not in str(e):
            print(f"Warning: Could not get git status: {e}")
        return []


def run_command(
    command: List[str],
    return_output: bool = False,
    check: bool = False,
    cwd: Optional[str] = None,
    timeout: int = 60,
    log_queue: Optional[Queue] = None,
) -> subprocess.CompletedProcess:
    """
    ! A more robust command runner that handles large outputs and potential hangs.
    It uses a timeout to prevent indefinite hangs and Popen with communicate
    to avoid pipe deadlocks, and supports real-time logging via a queue.
    """
    with subprocess_lock:
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

            return subprocess.CompletedProcess(
                command, process.returncode, stdout, stderr
            )

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
