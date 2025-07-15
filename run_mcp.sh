#!/bin/bash
# This script ensures that the MCP server is run with the correct python executable
# from the user's current environment on Unix-like systems.

# Get the directory of this script.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# ! We do NOT change the current directory anymore to allow running checks
# ! in other projects. The CWD of the caller is preserved.
# cd "$SCRIPT_DIR"

# Define the path to the venv activation script for Unix-like systems.
# This venv is for the development of AgentEnforcer itself.
VENV_PATH="$SCRIPT_DIR/venv/bin/activate"

if [ -f "$VENV_PATH" ]; then
  source "$VENV_PATH"
else
  echo "Warning: Virtual environment not found at $VENV_PATH. Using system python." >&2
fi

# Run the MCP server module directly using the activated python
python -m enforcer.mcp_server 