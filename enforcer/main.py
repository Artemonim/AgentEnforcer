import argparse
import os
from .core import Enforcer
from .config import load_config

def main():
    parser = argparse.ArgumentParser(description='Agent Enforcer: Code Quality Checker')
    parser.add_argument('path', nargs='?', default='.', help='Path to check (file or directory)')
    parser.add_argument('--ignore', help='Comma-separated rules to disable for this run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed issue list in the console')
    args = parser.parse_args()

    root_path = os.getcwd()  # Assume current dir is repo root
    config = load_config(root_path)
    if args.ignore:
        ignored = args.ignore.split(',')
        disabled = config.setdefault('disabled_rules', {})
        for rule in ignored:
            if ':' in rule:
                lang, r = rule.split(':', 1)
                disabled.setdefault(lang, []).append(r)
            else:
                disabled.setdefault('global', []).append(rule)
    enforcer = Enforcer(root_path, args.path, config, verbose=args.verbose)
    enforcer.run_checks()

if __name__ == '__main__':
    main() 