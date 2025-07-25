import json
import os
import platform
import re
import urllib.parse
import urllib.request
from typing import Any, List, Optional

import anyio
from fastmcp import FastMCP
from fastmcp.exceptions import NotFoundError
from fastmcp.prompts.prompt import FunctionPrompt, Message
from fastmcp.resources import Resource
from fastmcp.server.dependencies import get_context
from fastmcp.tools.tool import FunctionTool, Tool
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.types import Annotations, PromptMessage
from mcp.types import Resource as MCPResource
from pydantic import AnyUrl, Field

from .config import load_config
from .core import Enforcer
from .utils import get_git_modified_files, get_git_root


def _uri_to_path(uri: str) -> str:
    """
    Converts a file URI to a platform-native path, correcting for Windows path issues.
    """
    if not uri.startswith("file://"):
        return uri

    parsed_uri = urllib.parse.urlparse(uri)
    path = urllib.parse.unquote(parsed_uri.path)

    if platform.system() == "Windows":
        # On Windows, for a URI like 'file:///G:/foo/bar', the path becomes '/G:/foo/bar'.
        # We need to strip the leading slash to get a valid path 'G:/foo/bar'.
        if re.match(r"/\w:[/\\]", path):
            path = path[1:]

    return os.path.normpath(path)


# * Wrapper function without debug for production use
async def check_code_no_debug(
    resource_uris: Optional[List[str]] = None,
    check_git_modified_files: bool = False,
    verbose: bool = False,
    timeout_seconds: int = 0,
    root: Optional[str] = None,
) -> dict:
    """Runs a quality check on the specified files (production version without debug).

    Args:
        resource_uris (Optional[List[str]], optional): A list of file URIs to check. If omitted, the entire repository is checked. Ex: ["file:///G:/path/to/file.py"]. Defaults to None.
        check_git_modified_files (bool, optional): If true, ignores resource_uris and checks only the files modified in git. Defaults to False.
        verbose (bool, optional): If true, provides a detailed, file-by-file list of every issue. Essential for seeing specific error messages. Defaults to False.
        timeout_seconds (int, optional): The timeout for the check in seconds. Set to 0 to disable the timeout entirely. Defaults to 0.
        root (Optional[str], optional): The absolute path to the repository root. If omitted, attempts to auto-detect via git. If detection fails (e.g., not in a git repo), an error is returned requiring the parameter. Defaults to None.

    Returns:
        dict: A dictionary containing the results of the check, with keys like 'errors', 'warnings', and 'messages'.

    Example Usage:
        - Check the whole project with details:
          {"verbose": true, "root": "G:/GitHub/MyProject"}

        - Check a specific file and directory:
          {"resource_uris": ["file:///G:/GitHub/MyProject/src/main.py"], "verbose": true}

        - Check only the files I've changed:
          {"check_git_modified_files": true, "verbose": true}
    """
    return await check_code(
        resource_uris=resource_uris,
        check_git_modified_files=check_git_modified_files,
        verbose=verbose,
        timeout_seconds=timeout_seconds,
        debug=False,
        root=root,
    )


class FilePathResource(Resource):
    """A concrete resource that represents a file on disk."""

    file_path: str = Field(..., exclude=True)

    async def read(self) -> str | bytes:
        if not os.path.exists(self.file_path):
            raise NotFoundError(f"File not found: {self.file_path}")
        with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def to_mcp_resource(self, **overrides: Any) -> MCPResource:
        final_overrides = overrides.copy()
        if os.path.exists(self.file_path):
            final_overrides["size"] = os.path.getsize(self.file_path)
        return super().to_mcp_resource(**final_overrides)


async def check_code(
    resource_uris: Optional[List[str]] = None,
    check_git_modified_files: bool = False,
    verbose: bool = False,
    timeout_seconds: int = 0,
    debug: bool = False,
    root: Optional[str] = None,
) -> dict:
    """Runs a quality check on the specified files.

    Args:
        resource_uris (Optional[List[str]], optional): A list of file URIs to check. Defaults to None.
        check_git_modified_files (bool, optional): If true, ignores resource_uris and checks only modified files in git. Defaults to False.
        verbose (bool, optional): If true, provides a more detailed output. Defaults to False.
        timeout_seconds (int, optional): The timeout for the check in seconds. 0 means no timeout. Defaults to 0.
        debug (bool, optional): If true, enables debug mode for more verbose logs. Defaults to False.
        root (Optional[str], optional): The absolute path to the repository root. If not provided, it's auto-detected. Defaults to None.
    """
    try:
        # Determine root
        if not root:
            ctx = get_context()
            try:
                roots = await ctx.list_roots()
                if roots:
                    root = _uri_to_path(str(roots[0].uri))
            except Exception:
                # Fallback if client doesn't support roots/list
                pass

            if not root:
                git_root = get_git_root(timeout=5)
                if git_root and os.path.isdir(git_root):
                    root = git_root
                else:
                    return {
                        "error": "Could not auto-detect repository root. Please provide the 'root' parameter."
                    }

        if root and not os.path.isdir(root):
            return {"error": f"The provided root path is not a valid directory: {root}"}

        # Determine target paths
        target_paths = None
        if check_git_modified_files:
            git_timeout = (
                15 if timeout_seconds == 0 or timeout_seconds > 15 else timeout_seconds
            )
            target_paths = get_git_modified_files(cwd=root, timeout=git_timeout)
            if not target_paths:
                return {"messages": ["No modified files to check."]}
        elif resource_uris:
            target_paths = [str(uri).removeprefix("file:///") for uri in resource_uris]

        config = load_config(root)
        enforcer = Enforcer(
            root_path=root,
            target_paths=target_paths,
            config=config,
            verbose=verbose,
        )

        # If timeout, run with anyio timeout
        if timeout_seconds > 0:
            try:
                with anyio.fail_after(timeout_seconds):
                    return enforcer.run_checks_structured()
            except TimeoutError:
                return {"error": f"Check timed out after {timeout_seconds} seconds."}
        else:
            return enforcer.run_checks_structured()
    except Exception as e:
        import traceback

        return {
            "error": f"An unexpected error occurred in check_code: {e}\n{traceback.format_exc()}"
        }


class AgentEnforcerMCP(FastMCP[dict]):

    def __init__(self):
        super().__init__(
            "agent_enforcer",
            instructions="Agent Enforcer is a code quality checker that can lint and autofix code in multiple languages.",
        )

        # * Conditionally add checker based on config file
        debug_mode = False
        try:
            # ? We need the root to load config, but can't get it from context in sync __init__.
            # ? Using git root detection as a reliable fallback.
            root = get_git_root()
            if root:
                config = load_config(root)
                debug_mode = config.get("debug_mode_enabled", False)
        except Exception:
            # ! If git root or config fails, default to non-debug mode.
            pass  # Silently fail, assuming debug is off.

        if debug_mode:
            self.add_tool(FunctionTool.from_function(check_code, name="checker"))
        else:
            self.add_tool(
                FunctionTool.from_function(
                    check_code_no_debug,
                    name="checker",
                    description="Runs comprehensive code quality checks using multiple linters (black, isort, flake8, mypy, pyright) and returns structured results with errors, warnings, and suggestions for improvement.",
                )
            )

        # Add prompts
        def fix_this_file(file: str, issues: str) -> list[PromptMessage]:
            return [
                Message(
                    role="user",
                    content=f"You are a code fixer. Given a file with issues: {issues}, suggest fixes for {file}.",
                )
            ]

        self.add_prompt(
            FunctionPrompt.from_function(
                fix_this_file,
                name="fix-this-file",
                title="Fix Code Issues",
                description="Generates a structured prompt asking the AI to fix specific linting issues in a given file. Use this when you have lint errors and want the AI to suggest corrections.",
            )
        )

        def summarize_lint_errors(report: str) -> list[PromptMessage]:
            return [
                Message(
                    role="user",
                    content=f"Summarize the critical errors from this lint report: {report}.",
                )
            ]

        self.add_prompt(
            FunctionPrompt.from_function(
                summarize_lint_errors,
                name="summarize-lint-errors",
                title="Summarize Lint Errors",
                description="Creates a prompt asking the AI to summarize and prioritize the most critical errors from a lint report. Useful for getting a high-level overview of code quality issues.",
            )
        )

        def explain_rule(rule: str) -> list[PromptMessage]:
            return [
                Message(
                    role="user",
                    content=f"Explain the lint rule {rule} and provide examples of how to fix violations.",
                )
            ]

        self.add_prompt(
            FunctionPrompt.from_function(
                explain_rule,
                name="explain-rule",
                title="Explain Lint Rule",
                description="Generates a prompt asking the AI to explain a specific linting rule, why it's important, and provide examples of how to fix violations. Helpful for learning about code quality standards.",
            )
        )

    async def _list_resources(self) -> list[Resource]:
        ctx = get_context()
        roots = await ctx.list_roots()
        resources = []

        if not roots:
            return []

        # Assuming single root for now
        root_path = _uri_to_path(str(roots[0].uri))
        if not os.path.isdir(root_path):
            return []

        enforcer = Enforcer(root_path=root_path)
        files_by_lang, _ = enforcer.scan_files()

        for lang, files in files_by_lang.items():
            for file_path in files:
                rel_path = os.path.relpath(file_path, root_path)
                uri = f"file:///{file_path.replace(os.sep, '/')}"
                resources.append(
                    FilePathResource(
                        uri=AnyUrl(uri),
                        file_path=file_path,
                        name=rel_path,
                        description=f"{lang} file: {rel_path}",
                        mime_type="text/plain",
                    )
                )

        return resources


# This should be the only instantiation at the top level
mcp = AgentEnforcerMCP()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
