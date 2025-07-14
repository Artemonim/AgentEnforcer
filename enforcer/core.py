import os
import logging
import json
import shutil
import subprocess
import datetime
from .plugins import load_plugins
from .presenter import Presenter
import sys

# * Core class for Agent Enforcer
class Enforcer:
    def __init__(self, root_path, target_path=None, config=None):
        self.root_path = os.path.abspath(root_path)
        self.target_path = os.path.abspath(target_path) if target_path else self.root_path
        self.config = config or {}
        self.gitignore_path = os.path.join(self.root_path, '.gitignore')
        self.gitignore = self._load_gitignore()
        self.plugins = load_plugins()
        self.presenter = Presenter()
        self.detailed_logger, self.stats_logger = self.setup_logging()
        self.warned_missing = set()

    def _load_gitignore(self):
        if os.path.exists(self.gitignore_path):
            from gitignore_parser import parse_gitignore
            return parse_gitignore(self.gitignore_path, self.root_path)
        return lambda x: False

    def setup_logging(self):
        # Detailed log for the last check
        detailed_logger = logging.getLogger('enforcer.detailed')
        detailed_logger.setLevel(logging.DEBUG)
        if detailed_logger.hasHandlers(): detailed_logger.handlers.clear()
        fh_detailed = logging.FileHandler('Enforcer_last_check.log', mode='w', encoding='utf-8')
        detailed_logger.addHandler(fh_detailed)

        # Stats log for historical data
        stats_logger = logging.getLogger('enforcer.stats')
        stats_logger.setLevel(logging.INFO)
        if stats_logger.hasHandlers(): stats_logger.handlers.clear()
        fh_stats = logging.FileHandler('Enforcer_stats.log', mode='a', encoding='utf-8')
        stats_logger.addHandler(fh_stats)

        return detailed_logger, stats_logger

    def scan_files(self):
        files_by_lang = {}
        for root, dirs, files in os.walk(self.target_path):
            # Prune directories based on .gitignore
            dirs[:] = [d for d in dirs if not self.gitignore(os.path.join(root, d))]
            for file in files:
                file_path = os.path.join(root, file)
                if self.gitignore(file_path):
                    continue
                lang = self.get_language(file_path)
                if lang:
                    files_by_lang.setdefault(lang, []).append(file_path)
        return files_by_lang

    def get_language(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        for plugin in self.plugins.values():
            if ext in plugin.extensions:
                return plugin.language
        return None

    def run_checks(self):
        timestamp = datetime.datetime.now().isoformat()
        self.presenter.separator("Agent Enforcer")
        self.stats_logger.info(f"--- Check started at {timestamp} ---")

        files_by_lang = self.scan_files()
        if not files_by_lang:
            self.presenter.status("No files to check.", "warning")
            return {}

        total_errors = {}
        for lang, files in files_by_lang.items():
            self.presenter.separator(f"Language: {lang}")
            plugin = self.plugins[lang]

            if not self.check_tools(plugin):
                self.presenter.status(f"Skipping {lang} due to missing tools.", "warning")
                continue

            # Step 2: Autofix style
            self.presenter.status("Running auto-fixers...")
            fix_result = plugin.autofix_style(files, self.config.get('tool_configs', {}))
            changed_count = fix_result.get("changed_count", 0)
            if changed_count > 0:
                self.presenter.status(f"Formatted {changed_count} files.", "success")
            else:
                self.presenter.status("No style changes needed.")

            # Step 3: Lint
            self.presenter.status("Running linters and static analysis...")
            disabled = self.config.get('disabled_rules', {})
            lint_errors = plugin.lint(files, disabled.get(lang, []) + disabled.get('global', []), self.config.get('tool_configs', {}))

            self.presenter.display_errors(lint_errors, lang)
            if lint_errors:
                total_errors[lang] = lint_errors
                self.log_errors(lang, lint_errors, timestamp)
                self.presenter.status(f"Stopping further checks for {lang} due to critical issues.", "error")
                continue

            # Step 4: Compile
            self.presenter.status("Running compilation checks...")
            compile_errors = plugin.compile(files)
            if compile_errors:
                total_errors[lang] = compile_errors
                self.presenter.status(f"Compilation failed for {lang}", "error")
                # log errors...
                continue
            else:
                 self.presenter.status("Compilation successful.", "success")
            
            # Step 5: Test
            self.presenter.status("Running tests...")
            test_errors = plugin.test(self.root_path)
            if test_errors:
                total_errors[lang] = test_errors
                self.presenter.status(f"Tests failed for {lang}", "error")
                # log errors...
            else:
                self.presenter.status("All tests passed.", "success")


        self.presenter.separator("Summary")
        if not total_errors:
            self.presenter.status("All checks passed successfully!", "success")
        else:
            for lang, errors in total_errors.items():
                self.presenter.status(f"{lang}: {len(errors)} issues found.", "error")

        return total_errors

    def log_errors(self, lang, errors, timestamp):
        # Detailed log
        self.detailed_logger.debug(f"--- Errors for {lang} at {timestamp} ---")
        for error in errors:
            self.detailed_logger.debug(json.dumps(error))
            
        # Stats log: summarize with counts
        error_counts = {}
        for err in errors:
            err_type = f"[{err.get('tool', 'unknown')}] {err.get('rule', 'generic')}"
            error_counts[err_type] = error_counts.get(err_type, 0) + 1
            
        stats_summary = [f"{k} (x{v})" for k, v in sorted(error_counts.items())]
        self.stats_logger.info(f"{lang}: {', '.join(stats_summary)}")

    def check_tools(self, plugin):
        required_cmds = plugin.get_required_commands()
        all_found = True
        for cmd in required_cmds:
            if cmd in self.warned_missing:
                all_found = False
                continue
            
            if not shutil.which(cmd) and not (cmd == 'python' and shutil.which(sys.executable)):
                # Special check for './gradlew'
                if cmd == './gradlew' and os.path.exists(os.path.join(self.root_path, 'gradlew')):
                    continue

                self.warned_missing.add(cmd)
                self.presenter.status(f'Missing required tool: {cmd} for {plugin.language}. Please install it.', 'error')
                all_found = False

        return all_found

    def can_auto_install(self, cmd):
        return False

    def get_install_recommendation(self, cmd):
        recs = {
            'node': 'https://nodejs.org/',
            'dotnet': 'https://dotnet.microsoft.com/download',
            'gradlew': 'Ensure Gradle wrapper is present and executable in the repository root.',
        }
        return recs.get(cmd, 'Search for installation instructions online.') 