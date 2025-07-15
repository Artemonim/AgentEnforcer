import argparse
import os

from .config import load_config
from .core import Enforcer
from .mcp_server import mcp

# No longer calling the CLI, so this can be simplified.
# The main function is now only for running the MCP server.


def main():
    """
    Starts the FastMCP server for Agent Enforcer.
    """
    # The --root argument is no longer needed for the CLI wrapper,
    # as the MCP tool now handles the root path internally.
    # The main CLI entrypoint (`main.py`) handles its own argument parsing.
    mcp.run()


if __name__ == "__main__":
    main()
