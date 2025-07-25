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
        errors = []
        warnings = []

        # ktlint
        try:
            ktlint_result = run_command(
                ["./gradlew", "ktlintCheck"],
                return_output=True,
            )
            if ktlint_result.stdout:
                for line in ktlint_result.stdout.splitlines():
                    parts = line.split(":")
                    if len(parts) >= 4:
                        file_path = ":".join(parts[:-3])
                        line_num = parts[-3]
                        col = parts[-2]
                        msg = parts[-1].strip()
                        if root_path and file_path and os.path.isabs(file_path):
                            file_path = os.path.relpath(file_path, root_path)
                        errors.append(
                            {
                                "tool": "ktlint",
                                "file": file_path,
                                "line": int(line_num),
                                "message": msg,
                            }
                        )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            errors.append(
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
            if detekt_result.stdout:
                for line in detekt_result.stdout.splitlines():
                    if " - " in line:
                        loc_part, rest = line.split(" - ", 1)
                        loc_parts = loc_part.rsplit(":", 2)
                        if len(loc_parts) == 3:
                            file_path, line_num, col = loc_parts
                            if root_path and file_path and os.path.isabs(file_path):
                                file_path = os.path.relpath(file_path, root_path)
                            rule, message = rest.split(" - ", 1)
                            errors.append(
                                {
                                    "tool": "detekt",
                                    "file": file_path,
                                    "line": int(line_num),
                                    "message": message.strip(),
                                    "rule": rule.strip(),
                                }
                            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            errors.append(
                {
                    "tool": "detekt",
                    "file": "unknown",
                    "line": 0,
                    "message": "detekt failed",
                }
            )

        return {"errors": errors, "warnings": warnings}

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
