import json
import sys
from typing import List, Optional

from fastmcp import FastMCP

from .utils import run_command

mcp = FastMCP("agent_enforcer")


@mcp.tool()
def run_check(
    targets: Optional[str] = None,
    check_git_modified_files: bool = False,
    verbose: bool = False,
    timeout_seconds: int = 0,
    debug: bool = False,
) -> str:
    """
    Runs a quality check by calling the standalone 'enforcer-cli' tool.

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
    :return: A string containing the formatted results or an error message.
    """
    try:
        # Using sys.executable ensures we use the python from the correct venv
        command = [sys.executable, "-m", "enforcer.cli"]
        timeout = timeout_seconds if timeout_seconds > 0 else None

        if verbose:
            command.append("--verbose")

        if check_git_modified_files:
            # The CLI doesn't have a direct git modified flag, as it's a feature
            # of the enforcer core. We can let the core handle it by not passing paths.
            pass
        elif targets:
            try:
                # The CLI expects paths as separate arguments
                parsed_targets = json.loads(targets)
                if isinstance(parsed_targets, list):
                    command.extend(parsed_targets)
                else:
                    command.append(str(parsed_targets))
            except json.JSONDecodeError:
                command.append(targets)

        # We don't pass a log_queue anymore, we just capture output
        result = run_command(
            command,
            return_output=True,
            check=False,  # We handle the output ourselves
            timeout=timeout,
        )

        if result.returncode != 0:
            # On error, stderr is usually more informative
            return result.stderr or result.stdout

        return result.stdout

    except FileNotFoundError:
        return "Error: 'enforcer-cli' not found. Is the package installed correctly?"
    except Exception as e:
        # Catch timeout errors from run_command and other exceptions
        if debug and hasattr(e, "stdout") and e.stdout:
            return f"An exception occurred: {e}\n\n--- Captured Log ---\n{e.stdout}"
        return f"An exception occurred: {e}"


def main():
    mcp.run()


if __name__ == "__main__":
    main()
