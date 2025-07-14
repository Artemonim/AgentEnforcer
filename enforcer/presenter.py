import os

class Presenter:
    """Handles formatted console output."""

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

    def display_errors(self, errors: list, lang: str, limit=20):
        """Displays a summarized list of structured errors."""
        if not errors:
            self.status(f"No issues found in {lang} code", "success")
            return

        self.status(f"Found {len(errors)} issues in {lang} code:", "warning")

        for i, error in enumerate(errors):
            if i >= limit:
                self.status(
                    f"  ... and {len(errors) - limit} more issues. See Enforcer_last_check.log for details."
                )
                break

            file_path = error.get("file", "unknown_file").replace(os.getcwd() + os.sep, "")
            line = error.get("line", 0)
            message = error.get("message", "")
            rule = error.get("rule", "")
            tool = error.get("tool", "")

            location = f"{file_path}:{line}"
            rule_info = f" ({rule})" if rule else ""
            tool_info = f"[{tool}]"

            print(f"  {location:<40} {tool_info:<10} {message}{rule_info}") 