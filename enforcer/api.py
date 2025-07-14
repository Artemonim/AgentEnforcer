from .core import Enforcer
from .config import load_config
from .presenter import captured_output
import json

def run_enforcer(paths=None, root_path='.', config=None, verbose=False):
    config = config or load_config(root_path)
    enforcer = Enforcer(root_path, target_paths=paths, config=config, verbose=verbose)
    # The presenter, called inside run_checks, will handle printing to stdout.
    # We just return the structured data for potential programmatic use,
    # though it's not used by run_enforcer_as_string.
    return enforcer.run_checks()

def run_enforcer_as_string(*args, **kwargs):
    """
    Runs the enforcer and captures all console output as a single string.
    This is ideal for wrapping the tool in contexts like an MCP server
    where a simple string return value is desired.
    """
    with captured_output() as (stdout, stderr):
        run_enforcer(*args, **kwargs)
    
    # We return the captured standard output.
    # The presenter writes everything to stdout.
    output = stdout.getvalue()
    return output 