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

    def _output(self, message: str):
        """Prints to stdout."""
        print(message)

    def status(self, message: str, level: str = "info"):
        """Prints a status message with a prefix icon."""
        prefixes = {
            "info": "* ",
            "success": "✓ ",
            "warning": "! ",
            "error": "✗ ",
        }
        prefix = prefixes.get(level, "* ")
        self._output(f"{prefix}{message}")

    def separator(self, title: str = ""):
        """Prints a separator line with an optional title."""
        if title:
            self._output(f"\n{'═' * 20} {title.upper()} {'═' * 20}")
        else:
            self._output("═" * 60)

    def display_results(
        self, errors: list, warnings: list, lang: str, severities: Optional[dict] = None
    ):
        """Displays a summarized list of structured errors and warnings."""
        severities = severities or {}
        all_issues = errors + warnings
        final_errors = []
        final_warnings = []

        for issue in all_issues:
            rule = issue.get("rule")
            override = severities.get(rule)

            if override == "error":
                final_errors.append(issue)
            elif override == "warning":
                final_warnings.append(issue)
            elif override == "info":
                pass  # Or handle as a separate category if needed
            elif issue in errors:
                final_errors.append(issue)
            else:
                final_warnings.append(issue)

        if not final_errors and not final_warnings:
            self.status(f"No issues found in {lang} code", "success")
            return

        if final_errors:
            self.status(f"Found {len(final_errors)} error(s) in {lang} code:", "error")
            if self.verbose:
                self._print_issues(final_errors)
            else:
                self._print_grouped_summary(final_errors)

        if final_warnings:
            self.status(
                f"Found {len(final_warnings)} warning(s) in {lang} code:", "warning"
            )
            if self.verbose:
                self._print_issues(final_warnings, limit=10)
            else:
                self._print_grouped_summary(final_warnings, limit=10)

        return final_errors, final_warnings

    def _print_issues(self, issues: list, limit: Optional[int] = None):
        """Helper to print a list of issues with an optional limit."""
        for i, issue in enumerate(issues):
            if limit and i >= limit:
                self.status(
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

            self._output(f"  {location:<40} {tool_info:<10} {message}{rule_info}")

    def _print_grouped_summary(self, issues: list, limit: Optional[int] = None):
        """Prints a summary of issues grouped by file and rule."""
        grouped_by_file = defaultdict(lambda: defaultdict(list))
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
                self.status(
                    f"  ... and issues in {len(grouped_by_file) - limit} more files. Use -v for full details."
                )
                break

            total_issues_in_file = sum(len(lines) for lines in rules.values())
            self._output(f"  - {file_path} ({total_issues_in_file} issues):")
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
                self._output(f"    - {rule}{detail}")
            file_count += 1

    def final_summary(self, all_errors: list, all_warnings: list):
        self.separator("Summary")
        total_error_count = len(all_errors)
        total_warning_count = len(all_warnings)

        if not total_error_count and not total_warning_count:
            self.status("All checks passed successfully!", "success")
        else:
            if total_error_count:
                self.status(
                    f"Found a total of {total_error_count} error(s) across all files.",
                    "error",
                )
            if total_warning_count:
                self.status(
                    f"Found a total of {total_warning_count} warning(s) across all files.",
                    "warning",
                )

            files_with_errors = defaultdict(int)
            for error in all_errors:
                files_with_errors[error.get("file", "unknown")] += 1

            if len(files_with_errors) > 10:
                self._output("\n  Top 3 files with most errors:")
                top_3 = sorted(
                    files_with_errors.items(), key=lambda item: item[1], reverse=True
                )[:3]
                for file, count in top_3:
                    self._output(
                        f"    - {file.replace(os.getcwd() + os.sep, '')} ({count} errors)"
                    )

        self._output(
            "\n* For a detailed machine-readable report, see Enforcer_last_check.log"
        )
        self._output(
            "* You shoud use grep tool to analyze the log file. Don't read it - it's big."
        )
