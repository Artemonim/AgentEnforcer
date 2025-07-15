import argparse
import os

from .config import load_config
from .core import Enforcer


def main():
    parser = argparse.ArgumentParser(description="Agent Enforcer: Standalone CLI")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Paths to check (files or directories). Defaults to current directory.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed issue list in the console",
    )
    # ? Maybe add more CLI-specific arguments in the future, like --format=json
    args = parser.parse_args()

    root_path = os.getcwd()
    config = load_config(root_path)

    enforcer = Enforcer(
        root_path=root_path,
        target_paths=args.paths,
        config=config,
        verbose=args.verbose,
    )
    enforcer.run_checks()


if __name__ == "__main__":
    main()
