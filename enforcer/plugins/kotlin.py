import os
import re
import subprocess
from multiprocessing import Queue
from typing import List, Optional

from ..utils import run_command


class Plugin:
    language = "kotlin"
    extensions = [".kt", ".kts"]

    def get_required_commands(self):
        return ["./gradlew"]

    def autofix_style(
        self,
        files: List[str],
        tool_configs: Optional[dict] = None,
    ):
        try:
            run_command(
                ["./gradlew", "ktlintFormat", "--quiet"],
                return_output=False,
            )
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
        warnings = []

        # ktlint
        try:
            ktlint_result = run_command(
                ["./gradlew", "ktlintCheck"],
                return_output=True,
            )
            ktlint_pattern = re.compile(r"(.+):(\d+):(\d+):\s+(.+)")
            if ktlint_result.stdout:
                for line in ktlint_result.stdout.splitlines():
                    match = ktlint_pattern.match(line)
                    if match:
                        file_path = match.group(1)
                        if root_path and file_path and os.path.isabs(file_path):
                            file_path = os.path.relpath(file_path, root_path)
                        warnings.append(
                            {
                                "tool": "ktlint",
                                "file": file_path,
                                "line": int(match.group(2)),
                                "message": match.group(4).strip(),
                            }
                        )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            warnings.append(
                {
                    "tool": "ktlint",
                    "file": "unknown",
                    "line": 0,
                    "message": "ktlintCheck failed",
                }
            )

        # detekt
        try:
            detekt_result = run_command(
                ["./gradlew", "detekt"],
                return_output=True,
            )
            detekt_pattern = re.compile(r"(.+):(\d+):(\d+)\s+-\s+(.+)\s+-\s+(.+)")
            if detekt_result.stdout:
                for line in detekt_result.stdout.splitlines():
                    match = detekt_pattern.match(line)
                    if match:
                        file_path = match.group(1)
                        if root_path and file_path and os.path.isabs(file_path):
                            file_path = os.path.relpath(file_path, root_path)
                        warnings.append(
                            {
                                "tool": "detekt",
                                "file": file_path,
                                "line": int(match.group(2)),
                                "message": match.group(5).strip(),
                                "rule": match.group(4).strip(),
                            }
                        )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            warnings.append(
                {
                    "tool": "detekt",
                    "file": "unknown",
                    "line": 0,
                    "message": "detekt failed",
                }
            )

        return {"errors": [], "warnings": warnings}

    def compile(self, files: List[str]):
        try:
            result = run_command(["./gradlew", "assemble"], return_output=True)
            if result.returncode != 0:
                return [
                    {
                        "tool": "gradle-assemble",
                        "message": "Build failed. See logs for details.",
                    }
                ]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return [
                {
                    "tool": "gradle-assemble",
                    "message": "Build timed out or gradlew not found.",
                }
            ]
        return []

    def test(self, root_path: str):
        try:
            result = run_command(["./gradlew", "test"], return_output=True)
            if result.returncode != 0:
                return [
                    {
                        "tool": "gradle-test",
                        "message": "Tests failed. See logs for details.",
                    }
                ]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return [
                {
                    "tool": "gradle-test",
                    "message": "Tests timed out or gradlew not found.",
                }
            ]
        return []
