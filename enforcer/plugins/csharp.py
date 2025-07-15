import json
import os
import re
import subprocess
from multiprocessing import Queue
from typing import List, Optional

from ..utils import run_command


class Plugin:
    language = "csharp"
    extensions = [".cs"]

    def get_required_commands(self):
        return ["dotnet"]

    def autofix_style(
        self,
        files: List[str],
        tool_configs: Optional[dict] = None,
    ):
        try:
            run_command(["dotnet", "format"], return_output=False)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return {"changed_count": 0}

    def lint(
        self,
        files: List[str],
        disabled_rules: List[str],
        tool_configs: Optional[dict] = None,
        root_path: Optional[str] = None,
    ):
        return self._run_build(root_path)

    def compile(self, files: List[str]):
        return []

    def test(self, root_path: str):
        try:
            result = run_command(["dotnet", "test"], return_output=True)
            if result.returncode != 0:
                return [
                    {
                        "tool": "dotnet-test",
                        "message": result.stdout or result.stderr,
                    }
                ]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return []

    def _run_build(self, root_path: Optional[str] = None):
        errors = []
        warnings = []
        pattern = re.compile(
            r"(.+)\((\d+),(\d+)\):\s+(warning|error)\s+([A-Z0-9]+):\s+(.+)"
        )

        try:
            result = run_command(["dotnet", "build"], return_output=True)
            output = result.stdout + result.stderr

            for line in output.splitlines():
                match = pattern.match(line)
                if match:
                    file_path = match.group(1)
                    if root_path and file_path and os.path.isabs(file_path):
                        file_path = os.path.relpath(file_path, root_path)
                    issue = {
                        "tool": "dotnet-build",
                        "file": file_path,
                        "line": int(match.group(2)),
                        "message": match.group(6).strip(),
                        "rule": match.group(5),
                    }
                    if match.group(4) == "error":
                        errors.append(issue)
                    else:
                        warnings.append(issue)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            errors.append(
                {
                    "tool": "dotnet-build",
                    "file": "unknown",
                    "line": 0,
                    "message": str(e),
                }
            )

        return {"errors": errors, "warnings": warnings}
