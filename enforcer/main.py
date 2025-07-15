import argparse
import os
import sys

from .config import load_config, save_config
from .core import Enforcer
from .utils import get_git_modified_files


def main():
    parser = argparse.ArgumentParser(
        description="Agent Enforcer: Code Quality Checker",
        epilog=(
            """
Examples:
  agent-enforcer                 # Check all files in the current directory
  agent-enforcer src/            # Check all files in src/
  agent-enforcer main.py         # Check a single file
  agent-enforcer --ignore E501   # Temporarily disable rule E501 for this run
  agent-enforcer --ignore python:E501,js_ts:no-console  # Disable multiple rules
  agent-enforcer --verbose       # Show all issues in detail
  agent-enforcer --modified      # Check only files modified in git status
"""
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=None,
        help="Paths to check (files or directories). Defaults to current directory.",
    )
    parser.add_argument(
        "--ignore",
        metavar="RULES",
        help="Comma-separated rules to disable for this run. Example: --ignore E501,python:W291",
    )
    parser.add_argument(
        "--blacklist",
        nargs="+",
        metavar="RULE",
        help="Add one or more rules to the permanent blacklist in config.json.",
    )
    parser.add_argument(
        "--error",
        nargs="+",
        metavar="RULE",
        help="Set one or more rules to 'error' severity in config.json.",
    )
    parser.add_argument(
        "--warning",
        nargs="+",
        metavar="RULE",
        help="Set one or more rules to 'warning' severity in config.json.",
    )
    parser.add_argument(
        "--info",
        nargs="+",
        metavar="RULE",
        help="Set one or more rules to 'info' severity in config.json.",
    )
    parser.add_argument(
        "--modified",
        action="store_true",
        help="Check only files modified in git status.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed issue list in the console.",
    )
    args = parser.parse_args()

    root_path = os.getcwd()  # Assume current dir is repo root
    config = load_config(root_path)

    config_updated = False
    if args.blacklist:
        disabled = config.setdefault("disabled_rules", {})
        for rule in args.blacklist:
            if ":" in rule:
                lang, r = rule.split(":", 1)
                disabled.setdefault(lang, []).append(r)
            else:
                disabled.setdefault("global", []).append(rule)
        config_updated = True

    if args.error or args.warning or args.info:
        severities = config.setdefault("severity_overrides", {})
        if args.error:
            for rule in args.error:
                severities[rule] = "error"
        if args.warning:
            for rule in args.warning:
                severities[rule] = "warning"
        if args.info:
            for rule in args.info:
                severities[rule] = "info"
        config_updated = True

    if config_updated:
        save_config(root_path, config)
        print("Configuration updated.")
        # If no paths are provided with config changes, exit.
        if not args.paths:
            sys.exit(0)

    # Determine target paths, including git-modified-only option
    if args.modified:
        modified_files = get_git_modified_files()
        if not modified_files:
            print("No modified files found in git status.")
            sys.exit(0)
        target_paths = modified_files
    elif args.paths is not None:
        target_paths = args.paths
    else:
        target_paths = ["."]

    if args.ignore:
        ignored = args.ignore.split(",")
        disabled = config.setdefault("disabled_rules", {})
        for rule in ignored:
            if ":" in rule:
                lang, r = rule.split(":", 1)
                disabled.setdefault(lang, []).append(r)
            else:
                disabled.setdefault("global", []).append(rule)
    enforcer = Enforcer(root_path, target_paths, config, verbose=args.verbose)
    enforcer.run_checks()


if __name__ == "__main__":
    main()
