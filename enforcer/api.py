import io
import json
from contextlib import redirect_stdout
from typing import List, Optional

from .config import load_config
from .core import Enforcer
from .presenter import captured_output


def run_enforcer(paths=None, root_path=".", config=None, verbose=False):
    config = config or load_config(root_path)
    enforcer = Enforcer(root_path, target_paths=paths, config=config, verbose=verbose)
    # The presenter, called inside run_checks, will handle printing to stdout.
    # We just return the structured data for potential programmatic use,
    # though it's not used by run_enforcer_as_string.
    return enforcer.run_checks()


def run_enforcer_as_string(
    paths: Optional[List[str]] = None,
    root_path: str = ".",
    verbose: bool = False,
    log_collector: Optional[List[str]] = None,
) -> str:
    """
    A wrapper around the Enforcer class that captures its stdout for string output.
    """
    output_capture = io.StringIO()
    # The presenter will now print to stdout AND collect logs if a collector is provided.
    # We still redirect stdout to capture the final, formatted output for the return value.
    with redirect_stdout(output_capture):
        enforcer = Enforcer(
            root_path=root_path,
            target_paths=paths,
            verbose=verbose,
            log_collector=log_collector,
        )
        enforcer.run_checks()

    return output_capture.getvalue()
