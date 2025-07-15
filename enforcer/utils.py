import os
import subprocess
import threading
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
) -> subprocess.CompletedProcess:
    """
    ! A more robust command runner that handles large outputs and potential hangs.
    It uses a timeout to prevent indefinite hangs.
    """
    with subprocess_lock:
        try:
            process = subprocess.run(
                command,
                capture_output=return_output,
                text=True,
                check=check,
                cwd=cwd,
                encoding="utf-8",
                errors="ignore",
                timeout=120,  # * Add a generous timeout to prevent indefinite hangs
            )
            return process
        except FileNotFoundError as e:
            # Re-raise with a more informative message
            raise FileNotFoundError(f"Command not found: {command[0]}") from e
        except subprocess.CalledProcessError as e:
            # This is raised when check=True and the process returns a non-zero exit code.
            # The caller is expected to handle this.
            raise e
        except subprocess.TimeoutExpired as e:
            # Log the timeout and the command that caused it.
            # We can add more sophisticated logging later if needed.
            print(f"Warning: Command '{' '.join(command)}' timed out.")
            # Re-raise the exception so the caller can handle it.
            raise e
