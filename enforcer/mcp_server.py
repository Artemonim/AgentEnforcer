import json
import os
from typing import Any, List, Optional

import anyio
from fastmcp import FastMCP
from fastmcp.exceptions import NotFoundError
from fastmcp.prompts.prompt import FunctionPrompt, Message
from fastmcp.resources import Resource
from fastmcp.server.dependencies import get_context
from fastmcp.tools.tool import FunctionTool
from mcp.types import PromptMessage, Annotations, Resource as MCPResource
from mcp.server.lowlevel.helper_types import ReadResourceContents
from pydantic import AnyUrl, Field

from .config import load_config
from .core import Enforcer
from .utils import get_git_modified_files, get_git_root


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
            final_overrides['size'] = os.path.getsize(self.file_path)
        return super().to_mcp_resource(**final_overrides)


class AgentEnforcerMCP(FastMCP[dict]):

    def __init__(self):
        super().__init__(
            "agent_enforcer",
            instructions="Agent Enforcer is a code quality checker that can lint and autofix code in multiple languages.",
        )

        # Add checker tool
        self.add_tool(FunctionTool.from_function(self.check_code, name="checker"))

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
                description="Prompt to fix issues in a file based on lint results.",
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
                description="Summarize the most critical lint errors.",
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
                description="Explain a specific lint rule and how to fix it.",
            )
        )

    async def _list_resources(self) -> list[Resource]:
        ctx = get_context()
        roots = await ctx.list_roots()
        resources = []

        if not roots:
            return []

        # Assuming single root for now
        root_path = str(roots[0].uri).removeprefix("file://")
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

    async def check_code(
        self,
        resource_uris: Optional[List[str]] = None,
        check_git_modified_files: bool = False,
        verbose: bool = False,
        timeout_seconds: int = 0,
        debug: bool = False,
        root: Optional[str] = None,
    ) -> dict:
        """
        Runs a quality check on the specified files.
        """
        # Determine root
        if not root:
            ctx = get_context()
            roots = await ctx.list_roots()
            if roots:
                root = str(roots[0].uri).removeprefix("file://")
            else:
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


def main():
    mcp = AgentEnforcerMCP()
    mcp.run()


if __name__ == "__main__":
    main()
