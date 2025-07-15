import json
import re
import subprocess


class Plugin:
    language = "js_ts"
    extensions = [".js", ".ts", ".jsx", ".tsx"]

    def get_required_commands(self):
        return ["npx"]

    def autofix_style(self, files, tool_configs=None):
        for file in files:
            subprocess.run(["npx", "prettier", "--write", file], check=False)
        return {"changed_count": 0}

    def lint(self, files, disabled_rules, tool_configs=None):
        errors = []
        warnings = []

        # Use eslint's JSON formatter for reliable parsing
        cmd = ["npx", "eslint", "--format", "json"]
        cmd.extend(files)

        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

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

        return {"errors": errors, "warnings": warnings}

    def compile(self, files):
        # Run tsc on the project
        result = subprocess.run(
            ["npx", "tsc"], capture_output=True, text=True
        )  # Assumes tsconfig.json
        return result.stdout.splitlines() if result.returncode != 0 else []

    def test(self, root_path):
        try:
            result = subprocess.run(
                ["npx", "jest", root_path], check=True, capture_output=True, text=True
            )
            return []
        except subprocess.CalledProcessError as e:
            return e.output.splitlines()
        except FileNotFoundError:
            return []  # No tests
