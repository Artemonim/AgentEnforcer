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
        log_queue: Optional[Queue] = None,
    ):
        try:
            run_command(
                ["dotnet", "format"],
                return_output=False,
                log_queue=log_queue,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            if log_queue:
                log_queue.put(f"Error running dotnet format: {e}")
        return {"changed_count": 0}  # dotnet format doesn't reliably report changes

    def lint(
        self,
        files: List[str],
        disabled_rules: List[str],
        tool_configs: Optional[dict] = None,
        log_queue: Optional[Queue] = None,
        root_path: Optional[str] = None,
    ):
        # In C#, linting and compilation are often the same step.
        # We run build here and parse errors/warnings.
        return self._run_build(log_queue, root_path)

    def compile(self, files: List[str]):
        # This step is combined with lint for C# projects.
        # Returning no errors as build is handled in lint().
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
            pass  # Error is already logged by run_command
        return []

    def _run_build(
        self,
        log_queue: Optional[Queue] = None,
        root_path: Optional[str] = None,
    ):
        errors = []
        warnings = []
        # This regex captures the standard format of dotnet build errors/warnings
        # Example: C:\Path\File.cs(10,5): error CS0103: The name 'xyz' does not exist...
        pattern = re.compile(
            r"(.+)\((\d+),(\d+)\):\s+(warning|error)\s+([A-Z0-9]+):\s+(.+)"
        )

        try:
            result = run_command(
                ["dotnet", "build"],
                return_output=True,
                log_queue=log_queue,
            )
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
