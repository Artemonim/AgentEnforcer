import json
import os
import re
import subprocess
import sys
from multiprocessing import Queue
from typing import List, Optional

from ..utils import run_command


class Plugin:
    language = "python"
    extensions = [".py"]

    def get_required_commands(self):
        return ["python"]

    def autofix_style(
        self,
        files: List[str],
        tool_configs: Optional[dict] = None,
    ):
        tool_configs = tool_configs or {}
        changed_files = set()

        # Run black
        try:
            black_cmd = [sys.executable, "-m", "black", "--quiet"]
            if "black" in tool_configs:
                black_cmd.extend(["--config", tool_configs["black"]])
            black_cmd.extend(files)
            black_res = run_command(black_cmd, return_output=True)
            if black_res.stderr:
                changed_files.update(re.findall(r"reformatted (.+)", black_res.stderr))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Errors are handled by run_command's logging, just pass
            pass

        # Run isort
        try:
            isort_cmd = [sys.executable, "-m", "isort", "--quiet"]
            if "isort" in tool_configs:
                isort_cmd.extend(["--settings-path", tool_configs["isort"]])
            isort_cmd.extend(files)
            isort_res = run_command(isort_cmd, return_output=True)
            if isort_res.stderr:
                changed_files.update(re.findall(r"Fixing (.+)", isort_res.stderr))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return {"changed_count": len(changed_files)}

    def lint(
        self,
        files: List[str],
        disabled_rules: List[str],
        tool_configs: Optional[dict] = None,
        root_path: Optional[str] = None,
    ):
        tool_configs = tool_configs or {}
        errors = []
        warnings = []

        # Pyright
        try:
            pyright_cmd = [sys.executable, "-m", "pyright", "--outputjson"]
            pyright_cmd.extend(files)
            pyright_res = run_command(pyright_cmd, return_output=True)
            if pyright_res.stdout:
                try:
                    pyright_data = json.loads(pyright_res.stdout)
                    for diag in pyright_data.get("generalDiagnostics", []):
                        file_path = diag.get("file")
                        if root_path and file_path and os.path.isabs(file_path):
                            file_path = os.path.relpath(file_path, root_path)
                        issue = {
                            "tool": "pyright",
                            "file": file_path,
                            "line": diag.get("range", {})
                            .get("start", {})
                            .get("line", 0)
                            + 1,
                            "message": diag.get("message"),
                            "rule": diag.get("rule", ""),
                        }
                        if diag.get("severity") == "error":
                            errors.append(issue)
                        elif diag.get("severity") == "warning":
                            warnings.append(issue)
                except json.JSONDecodeError:
                    errors.append(
                        {
                            "tool": "pyright",
                            "file": "unknown",
                            "line": 0,
                            "message": "Failed to parse pyright JSON output",
                        }
                    )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            errors.append(
                {"tool": "pyright", "file": "unknown", "line": 0, "message": str(e)}
            )

        # flake8
        try:
            flake8_cmd = [
                sys.executable,
                "-m",
                "flake8",
                f'--ignore={",".join(disabled_rules)}',
            ]
            if "flake8" in tool_configs:
                flake8_cmd.extend(["--config", tool_configs["flake8"]])
            flake8_cmd.extend(files)
            flake8_res = run_command(flake8_cmd, return_output=True)
            if flake8_res.stdout:
                for line in flake8_res.stdout.splitlines():
                    match = re.match(r"([^:]+):(\d+):(\d+): ([EFWC]\d+) (.+)", line)
                    if match:
                        code = match.group(4)
                        file_path = match.group(1)
                        if root_path and file_path and os.path.isabs(file_path):
                            file_path = os.path.relpath(file_path, root_path)
                        issue = {
                            "tool": "flake8",
                            "file": file_path,
                            "line": int(match.group(2)),
                            "message": match.group(5).strip(),
                            "rule": code,
                        }
                        if code.startswith("E") or code.startswith("F"):
                            errors.append(issue)
                        else:
                            warnings.append(issue)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            errors.append(
                {"tool": "flake8", "file": "unknown", "line": 0, "message": str(e)}
            )

        # mypy - all are errors
        try:
            mypy_cmd = [sys.executable, "-m", "mypy"]
            if "mypy" in tool_configs:
                mypy_cmd.extend(["--config-file", tool_configs["mypy"]])
            mypy_cmd.extend(files)
            mypy_res = run_command(mypy_cmd, return_output=True)
            if mypy_res.stdout:
                for line in mypy_res.stdout.splitlines():
                    match = re.match(r"([^:]+):(\d+): error: (.+)", line)
                    if match:
                        message = match.group(3).strip()
                        rule_match = re.search(r"\[(.+)\]$", message)
                        rule = rule_match.group(1) if rule_match else ""
                        if rule_match:
                            message = message[: -len(rule_match.group(0))].strip()

                        file_path = match.group(1)
                        if root_path and file_path and os.path.isabs(file_path):
                            file_path = os.path.relpath(file_path, root_path)

                        errors.append(
                            {
                                "tool": "mypy",
                                "file": file_path,
                                "line": int(match.group(2)),
                                "message": message,
                                "rule": rule,
                            }
                        )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            errors.append(
                {"tool": "mypy", "file": "unknown", "line": 0, "message": str(e)}
            )

        return {"errors": errors, "warnings": warnings}
