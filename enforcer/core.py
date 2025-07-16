import datetime
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from multiprocessing import Queue
from typing import Optional

from .plugins import load_plugins
from .presenter import Presenter


# * Core class for Agent Enforcer
class Enforcer:
    def __init__(
        self,
        root_path,
        target_paths=None,
        config=None,
        verbose=False,
    ):
        self.root_path = os.path.abspath(root_path)
        # * Change CWD to ensure all relative paths and tools work correctly
        os.chdir(self.root_path)

        if target_paths:
            self.target_paths = [
                os.path.abspath(os.path.join(self.root_path, p)) for p in target_paths
            ]
        else:
            self.target_paths = [self.root_path]

        self.config = config or {}
        self.verbose = verbose
        self.gitignore_path = os.path.join(self.root_path, ".gitignore")
        self.gitignore = self._load_gitignore()
        self.plugins = load_plugins()
        self.presenter = Presenter(verbose=self.verbose)
        self.warned_missing: set[str] = set()

    def _load_gitignore(self):
        if os.path.exists(self.gitignore_path):
            from gitignore_parser import parse_gitignore  # type: ignore

            return parse_gitignore(self.gitignore_path, self.root_path)
        return lambda x: False

    def setup_logging(self):
        # Detailed log for the last check
        detailed_logger = logging.getLogger("enforcer.detailed")
        detailed_logger.setLevel(logging.DEBUG)
        if detailed_logger.hasHandlers():
            detailed_logger.handlers.clear()
        fh_detailed = logging.FileHandler(
            "Enforcer_last_check.log", mode="w", encoding="utf-8"
        )
        detailed_logger.addHandler(fh_detailed)

        # Stats log for historical data
        stats_logger = logging.getLogger("enforcer.stats")
        stats_logger.setLevel(logging.INFO)
        if stats_logger.hasHandlers():
            stats_logger.handlers.clear()
        fh_stats = logging.FileHandler("Enforcer_stats.log", mode="a", encoding="utf-8")
        stats_logger.addHandler(fh_stats)

        return detailed_logger, stats_logger

    def scan_files(self):
        files_by_lang = {}
        messages = []

        for path in self.target_paths:
            if not os.path.exists(path):
                messages.append(f"Path does not exist: {path}")
                continue
            if os.path.isfile(path):
                if self.gitignore(path):
                    continue
                lang = self.get_language(path)
                if lang:
                    files_by_lang.setdefault(lang, []).append(path)
                else:
                    messages.append(f"No supported language for file: {path}")
            elif os.path.isdir(path):
                has_files = False
                for root, dirs, files in os.walk(path):
                    # Prune directories based on .gitignore
                    dirs[:] = [
                        d for d in dirs if not self.gitignore(os.path.join(root, d))
                    ]
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self.gitignore(file_path):
                            continue
                        lang = self.get_language(file_path)
                        if lang:
                            files_by_lang.setdefault(lang, []).append(file_path)
                            has_files = True
                if not has_files:
                    messages.append(f"No supported files in directory: {path}")

        # Remove duplicates if paths overlap
        for lang in files_by_lang:
            files_by_lang[lang] = sorted(list(set(files_by_lang[lang])))

        return files_by_lang, messages

    def get_language(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        for plugin in self.plugins.values():
            if ext in plugin.extensions:
                # * Make path relative for presenter display
                plugin.relative_path = os.path.relpath(file_path, self.root_path)
                return plugin.language
        return None

    def run_checks(self):
        self.detailed_logger, self.stats_logger = self.setup_logging()
        timestamp = datetime.datetime.now().isoformat()
        self.presenter.separator("Agent Enforcer")
        self.stats_logger.info(f"--- Check started at {timestamp} ---")

        files_by_lang, messages = self.scan_files()
        if messages:
            self.presenter.status("\n".join(messages), "warning")
        if not files_by_lang:
            if messages:
                self.presenter.status("\n".join(messages), "warning")
            else:
                self.presenter.status("No files to check.", "warning")
            return self.presenter.get_output()

        total_errors_list = []
        total_warnings_list = []

        for lang, files in files_by_lang.items():
            self.presenter.separator(f"Language: {lang}")
            plugin = self.plugins.get(lang)

            if not plugin or not self.check_tools(plugin):
                self.presenter.status(
                    f"Skipping {lang} due to missing plugin or tools.", "warning"
                )
                continue

            # Autofix
            self.presenter.status("Running auto-fixers...")
            fix_result = plugin.autofix_style(
                files,
                self.config.get("tool_configs", {}),
            )
            changed_count = fix_result.get("changed_count", 0)
            self.presenter.status(
                f"Formatted {changed_count} files."
                if changed_count > 0
                else "No style changes needed."
            )

            # Lint
            self.presenter.status("Running linters and static analysis...")
            disabled = self.config.get("disabled_rules", {})
            severities = self.config.get("severity_overrides", {})
            lint_result = plugin.lint(
                files,
                disabled.get(lang, []) + disabled.get("global", []),
                self.config.get("tool_configs", {}),
                root_path=self.root_path,
            )
            # * Presenter needs relative paths, so we convert them here.
            for issue in lint_result.get("errors", []) + lint_result.get(
                "warnings", []
            ):
                if "file" in issue and os.path.isabs(issue["file"]):
                    try:
                        issue["file"] = os.path.relpath(issue["file"], self.root_path)
                    except ValueError:
                        # Keep absolute if it's on a different drive or other error
                        pass

            lang_errors = lint_result.get("errors", [])
            lang_warnings = lint_result.get("warnings", [])

            final_errors, final_warnings = self.presenter.display_results(
                lang_errors, lang_warnings, lang, severities
            )
            total_errors_list.extend(final_errors)
            total_warnings_list.extend(final_warnings)

            self.log_issues(lang, lang_errors, lang_warnings)

        self.presenter.final_summary(total_errors_list, total_warnings_list)

        return self.presenter.get_output()

    def run_checks_structured(self):
        self.detailed_logger, self.stats_logger = self.setup_logging()
        timestamp = datetime.datetime.now().isoformat()
        self.stats_logger.info(f"--- Check started at {timestamp} ---")

        files_by_lang, messages = self.scan_files()
        if not files_by_lang:
            return {
                "errors": [],
                "warnings": [],
                "messages": messages or ["No files to check."],
            }

        total_errors_list = []
        total_warnings_list = []

        for lang, files in files_by_lang.items():
            plugin = self.plugins.get(lang)

            if not plugin or not self.check_tools(plugin):
                continue

            # Autofix
            fix_result = plugin.autofix_style(
                files,
                self.config.get("tool_configs", {}),
            )

            # Lint
            disabled = self.config.get("disabled_rules", {})
            lint_result = plugin.lint(
                files,
                disabled.get(lang, []) + disabled.get("global", []),
                self.config.get("tool_configs", {}),
                root_path=self.root_path,
            )

            lang_errors = lint_result.get("errors", [])
            lang_warnings = lint_result.get("warnings", [])

            # Convert absolute to relative paths
            for issue in lang_errors + lang_warnings:
                if "file" in issue and os.path.isabs(issue["file"]):
                    try:
                        issue["file"] = os.path.relpath(issue["file"], self.root_path)
                    except ValueError:
                        pass

            total_errors_list.extend(lang_errors)
            total_warnings_list.extend(lang_warnings)

            self.log_issues(lang, lang_errors, lang_warnings)

        return {
            "errors": total_errors_list,
            "warnings": total_warnings_list,
            "messages": messages,
            "formatted_files": fix_result.get("changed_count", 0),
        }

    def log_issues(self, lang, errors, warnings):
        # Detailed log
        for issue in errors + warnings:
            self.detailed_logger.debug(json.dumps(issue))

        # Ensure logs are written immediately
        for handler in self.detailed_logger.handlers:
            handler.flush()

        # Stats log
        stats = {}
        for issue in errors + warnings:
            issue_type = (
                f"[{issue.get('tool', 'unknown')}] {issue.get('rule', 'generic')}"
            )
            stats[issue_type] = stats.get(issue_type, 0) + 1

        for issue_type, count in sorted(stats.items()):
            self.stats_logger.info(f"{lang}: {issue_type} (x{count})")

    def check_tools(self, plugin):
        required_cmds = plugin.get_required_commands()
        all_found = True
        for cmd in required_cmds:
            if cmd in self.warned_missing:
                all_found = False
                continue

            if not shutil.which(cmd) and not (
                cmd == "python" and shutil.which(sys.executable)
            ):
                # Special check for './gradlew'
                if cmd == "./gradlew" and os.path.exists(
                    os.path.join(self.root_path, "gradlew")
                ):
                    continue

                self.warned_missing.add(cmd)
                self.presenter.status(
                    f"Missing required tool: {cmd} for {plugin.language}. Please install it.",
                    "error",
                )
                all_found = False

        return all_found

    def can_auto_install(self, cmd):
        return False

    def get_install_recommendation(self, cmd):
        recs = {
            "node": "https://nodejs.org/",
            "dotnet": "https://dotnet.microsoft.com/download",
            "gradlew": "Ensure Gradle wrapper is present and executable in the repository root.",
        }
        return recs.get(cmd, "Search for installation instructions online.")
