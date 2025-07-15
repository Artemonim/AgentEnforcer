import json
import os
import re
import subprocess
from multiprocessing import Queue
from typing import List, Optional

from ..utils import run_command


class Plugin:
    language = "js_ts"
    extensions = [".js", ".ts", ".jsx", ".tsx"]

    def get_required_commands(self):
        return ["npx"]

    def autofix_style(
        self,
        files: List[str],
        tool_configs: Optional[dict] = None,
    ):
        try:
            cmd = ["npx", "prettier", "--write"]
            cmd.extend(files)
            run_command(cmd, return_output=False)
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

        try:
            # Use eslint's JSON formatter for reliable parsing
            cmd = ["npx", "eslint", "--format", "json"]
            cmd.extend(files)

            result = run_command(cmd, return_output=True)

            # Even with --format json, eslint might print to stderr on config errors
            if result.returncode != 0 and not result.stdout.strip():
                errors.append(
                    {
                        "tool": "eslint",
                        "file": "config",
                        "line": 0,
                        "message": result.stderr,
                    }
                )
                return {"errors": errors, "warnings": warnings}

            try:
                report = json.loads(result.stdout)
                for file_report in report:
                    file_path = file_report.get("filePath", "unknown")
                    if root_path and file_path and os.path.isabs(file_path):
                        file_path = os.path.relpath(file_path, root_path)
                    for message in file_report.get("messages", []):
                        issue = {
                            "tool": "eslint",
                            "file": file_path,
                            "line": message.get("line", 0),
                            "message": message.get("message", "Unknown issue"),
                            "rule": message.get("ruleId", "unknown-rule"),
                        }
                        if message.get("severity") == 2:  # 2 is error
                            errors.append(issue)
                        else:  # 1 is warning
                            warnings.append(issue)
            except json.JSONDecodeError:
                errors.append(
                    {
                        "tool": "eslint",
                        "file": "parser",
                        "line": 0,
                        "message": "Failed to parse ESLint JSON output.",
                    }
                )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            errors.append(
                {"tool": "eslint", "file": "unknown", "line": 0, "message": str(e)}
            )

        return {"errors": errors, "warnings": warnings}

    def compile(self, files: List[str]):
        try:
            # Run tsc on the project
            result = run_command(
                ["npx", "tsc"], return_output=True
            )  # Assumes tsconfig.json
            return result.stdout.splitlines() if result.returncode != 0 else []
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ["TSC command timed out or was not found."]

    def test(self, root_path: str):
        try:
            result = run_command(
                ["npx", "jest", root_path], check=True, return_output=True
            )
            return []
        except subprocess.CalledProcessError as e:
            return e.output.splitlines()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ["Jest command timed out or was not found."]
