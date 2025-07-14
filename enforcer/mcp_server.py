from .api import run_enforcer_as_string
from .utils import get_git_modified_files
from fastmcp import FastMCP
import asyncio
from typing import List, Optional
import json

mcp = FastMCP('agent-enforcer-server')

@mcp.tool()
def run_check(targets: Optional[str] = None, check_git_modified_files: bool = False, verbose: bool = False) -> str:
    """
    Runs a quality check on specified files, directories, or git-modified files.

    The tool can be run in one of three modes:
    1. Git Modified: Set 'check_git_modified_files' to True to check files reported as modified by git.
    2. Specific Targets: Provide a JSON string array of file or directory paths in 'targets'.
    3. Full Project: If neither of the above is provided, it checks the entire project directory.

    :param targets: A JSON string representing a list of relative paths (e.g., '["src/main.py", "tests/"]').
    :param check_git_modified_files: If True, ignores 'targets' and checks files modified in git.
    :param verbose: If True, provides a detailed, file-by-file list of all issues instead of a summary.
    :return: A string containing the formatted results of the check, similar to the console output.
    """
    paths_to_check = None
    
    if check_git_modified_files:
        paths_to_check = get_git_modified_files()
        if not paths_to_check:
            return "No modified files found in git status to check."
    elif targets:
        try:
            # The 'targets' parameter arrives as a JSON-encoded string.
            # We need to parse it back into a Python list.
            parsed_targets = json.loads(targets)
            if isinstance(parsed_targets, list):
                paths_to_check = parsed_targets
            else:
                # Handle cases where a single path string is sent without being a JSON array
                paths_to_check = [str(parsed_targets)]
        except json.JSONDecodeError:
            # If it's not valid JSON, treat it as a single, raw path string.
            paths_to_check = [targets]
    
    # If paths_to_check is still None, it will default to the project root inside run_enforcer.
    # The root_path for the enforcer will be '.' (current directory).
    return run_enforcer_as_string(paths=paths_to_check, root_path='.', verbose=verbose)

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main() 