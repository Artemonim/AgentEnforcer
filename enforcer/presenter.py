import os
from collections import defaultdict

class Presenter:
    """Handles formatted console output."""

    def __init__(self, verbose=False):
        self.verbose = verbose

    def status(self, message: str, level: str = "info"):
        """Prints a status message with a prefix icon."""
        prefixes = {
            "info": "* ",
            "success": "✓ ",
            "warning": "! ",
            "error": "✗ ",
        }
        prefix = prefixes.get(level, "* ")
        print(f"{prefix}{message}")

    def separator(self, title: str = ""):
        """Prints a separator line with an optional title."""
        if title:
            print(f"\n{'═' * 20} {title.upper()} {'═' * 20}")
        else:
            print("═" * 60)

    def display_results(self, errors: list, warnings: list, lang: str):
        """Displays a summarized list of structured errors and warnings."""
        if not errors and not warnings:
            self.status(f"No issues found in {lang} code", "success")
            return

        if errors:
            self.status(f"Found {len(errors)} error(s) in {lang} code:", "error")
            if self.verbose:
                self._print_issues(errors)
            else:
                self._print_grouped_summary(errors)
        
        if warnings:
            self.status(f"Found {len(warnings)} warning(s) in {lang} code:", "warning")
            if self.verbose:
                self._print_issues(warnings, limit=10)
            else:
                self._print_grouped_summary(warnings, limit=10)

    def _print_issues(self, issues: list, limit: int = None):
        """Helper to print a list of issues with an optional limit."""
        for i, issue in enumerate(issues):
            if limit and i >= limit:
                self.status(
                    f"  ... and {len(issues) - limit} more warnings. See Enforcer_last_check.log for details."
                )
                break
            
            file_path = issue.get("file", "unknown_file").replace(os.getcwd() + os.sep, "")
            line = issue.get("line", 0)
            message = issue.get("message", "")
            rule = issue.get("rule", "")
            tool = issue.get("tool", "")

            location = f"{file_path}:{line}"
            rule_info = f" ({rule})" if rule else ""
            tool_info = f"[{tool}]"

            print(f"  {location:<40} {tool_info:<10} {message}{rule_info}")
    
    def _print_grouped_summary(self, issues: list, limit: int = None):
        """Prints a summary of issues grouped by file and rule."""
        grouped_by_file = defaultdict(lambda: defaultdict(int))
        for issue in issues:
            file_path = issue.get("file", "unknown_file").replace(os.getcwd() + os.sep, "")
            rule_id = f"[{issue.get('tool', 'n/a')}][{issue.get('rule', 'n/a')}]"
            grouped_by_file[file_path][rule_id] += 1
        
        file_count = 0
        for file_path, rules in sorted(grouped_by_file.items()):
            if limit and file_count >= limit:
                self.status(f"  ... and issues in {len(grouped_by_file) - limit} more files. Use -v for full details.")
                break
            
            total_issues_in_file = sum(rules.values())
            print(f"  - {file_path} ({total_issues_in_file} issues):")
            for rule, count in sorted(rules.items()):
                print(f"    - {rule} (x{count})")
            file_count += 1
    
    def final_summary(self, all_errors, all_warnings):
        self.separator("Summary")
        total_error_count = sum(len(e) for e in all_errors.values())
        total_warning_count = sum(len(w) for w in all_warnings.values())

        if not total_error_count and not total_warning_count:
            self.status("All checks passed successfully!", "success")
        else:
            if total_error_count:
                 self.status(f"Found a total of {total_error_count} error(s) across all files.", "error")
            if total_warning_count:
                 self.status(f"Found a total of {total_warning_count} warning(s) across all files.", "warning")

            files_with_errors = defaultdict(int)
            for lang_errors in all_errors.values():
                for error in lang_errors:
                    files_with_errors[error.get("file", "unknown")] += 1
            
            if len(files_with_errors) > 10:
                print("\n  Top 3 files with most errors:")
                top_3 = sorted(files_with_errors.items(), key=lambda item: item[1], reverse=True)[:3]
                for file, count in top_3:
                    print(f"    - {file.replace(os.getcwd() + os.sep, '')} ({count} errors)")
        
        print("\n* For a detailed machine-readable report, see Enforcer_last_check.log")
        print("* You can use tools like `grep` to analyze the log file.") 