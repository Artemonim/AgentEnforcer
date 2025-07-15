import io
import os
import sys
from collections import defaultdict
from contextlib import contextmanager
from typing import List, Optional


@contextmanager
def captured_output():
    new_out, new_err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class Presenter:
    """Handles formatted console output."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.output_buffer: list[str] = []

    def _output(self, message: str):
        """Prints to stdout."""
        print(message)

    def status(self, message: str, level: str = "info"):
        """Prints a status message with a prefix icon."""
        icon_map = {"info": "i", "warning": "!", "error": "!!"}
        self.output_buffer.append(f"[{icon_map.get(level, 'i')}] {message}")

    def separator(self, title: str = ""):
        """Prints a separator line with an optional title."""
        self.output_buffer.append(f"\n--- {title} ---")

    def display_results(
        self, errors: list, warnings: list, lang: str, severities: Optional[dict] = None
    ):
        """Displays a summarized list of structured errors and warnings."""
        severities = severities or {}
        final_errors = []
        final_warnings = []

        def get_severity(rule, lang, severities):
            return severities.get(f"{lang}:{rule}", severities.get(rule, "warning"))

        for issue_type, issues in [("error", errors), ("warning", warnings)]:
            if not issues:
                continue

            self.output_buffer.append(f"\n{issue_type.capitalize()}s:")
            for issue in sorted(issues, key=lambda x: x.get("file", "")):
                file = issue.get("file", "general")
                line = issue.get("line", 0)
                col = issue.get("col", 0)
                rule = issue.get("rule", "unknown")
                msg = issue.get("message", "No message.")
                severity = get_severity(rule, lang, severities)

                formatted_issue = (
                    f"  - [{severity.upper()}] {file}:{line}:{col} {msg} ({rule})"
                )
                self.output_buffer.append(formatted_issue)

                if severity == "error":
                    final_errors.append(issue)
                else:  # warning or info
                    final_warnings.append(issue)

        return final_errors, final_warnings

    def _print_issues(self, issues: list, limit: Optional[int] = None):
        """Helper to print a list of issues with an optional limit."""
        for i, issue in enumerate(issues):
            if limit and i >= limit:
                self.output_buffer.append(
                    f"  ... and {len(issues) - limit} more warnings. See Enforcer_last_check.log for details."
                )
                break

            file_path = issue.get("file", "unknown_file").replace(
                os.getcwd() + os.sep, ""
            )
            line = issue.get("line", 0)
            message = issue.get("message", "")
            rule = issue.get("rule", "")
            tool = issue.get("tool", "")

            location = f"{file_path}:{line}"
            rule_info = f" ({rule})" if rule else ""
            tool_info = f"[{tool}]"

            self.output_buffer.append(
                f"  {location:<40} {tool_info:<10} {message}{rule_info}"
            )

    def _print_grouped_summary(self, issues: list, limit: Optional[int] = None):
        """Prints a summary of issues grouped by file and rule."""
        grouped_by_file: defaultdict[str, defaultdict[str, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for issue in issues:
            file_path = issue.get("file", "unknown_file").replace(
                os.getcwd() + os.sep, ""
            )
            rule_id = f"[{issue.get('tool', 'n/a')}][{issue.get('rule', 'n/a')}]"
            line = str(issue.get("line", "N/A"))
            grouped_by_file[file_path][rule_id].append(line)

        file_count = 0
        for file_path, rules in sorted(grouped_by_file.items()):
            if limit and file_count >= limit:
                self.output_buffer.append(
                    f"  ... and issues in {len(grouped_by_file) - limit} more files. Use -v for full details."
                )
                break

            total_issues_in_file = sum(len(lines) for lines in rules.values())
            self.output_buffer.append(
                f"  - {file_path} ({total_issues_in_file} issues):"
            )
            for rule, lines in sorted(rules.items()):
                count = len(lines)
                unique_lines = sorted(
                    set(lines), key=lambda x: int(x) if x.isdigit() else 9999
                )
                if count <= 3 and unique_lines and unique_lines[0] != "N/A":
                    lines_str = ", ".join(unique_lines)
                    detail = f" at line{'s' if count > 1 else ''} {lines_str}"
                else:
                    detail = f" (x{count})"
                self.output_buffer.append(f"    - {rule}{detail}")
            file_count += 1

    def final_summary(self, all_errors: list, all_warnings: list):
        error_count = len(all_errors)
        warning_count = len(all_warnings)

        summary = f"\n--- Summary ---\n"
        summary += f"Total Errors: {error_count}\n"
        summary += f"Total Warnings: {warning_count}"
        self.output_buffer.append(summary)

        if error_count > 0:
            self.output_buffer.append("\n! Check failed with errors.")
        else:
            self.output_buffer.append("\n* Check passed.")

        files_with_errors: defaultdict[str, int] = defaultdict(int)
        for error in all_errors:
            files_with_errors[error.get("file", "unknown")] += 1

        if len(files_with_errors) > 10:
            self.output_buffer.append("\n  Top 3 files with most errors:")
            top_3 = sorted(
                files_with_errors.items(), key=lambda item: item[1], reverse=True
            )[:3]
            for file, count in top_3:
                self.output_buffer.append(
                    f"    - {file.replace(os.getcwd() + os.sep, '')} ({count} errors)"
                )

        self.output_buffer.append(
            "\n* For a detailed machine-readable report, see Enforcer_last_check.log"
        )
        self.output_buffer.append(
            "* You shoud use grep tool to analyze the log file. Don't read it - it's big."
        )

    def get_output(self) -> str:
        return "\n".join(self.output_buffer)
