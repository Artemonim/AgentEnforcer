#!/bin/bash
# This script ensures that the MCP server is run with the correct python executable
# from the user's current environment. This avoids issues where 'agent-enforcer-mcp'
# might not be in the PATH that Cursor's environment can see.

# Find the directory where the script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# We assume a virtual environment 'venv' exists in the project root.
# We'll activate it to make sure we use the right python and dependencies.
VENV_PATH="$SCRIPT_DIR/venv/bin/activate"

if [ -f "$VENV_PATH" ]; then
  source "$VENV_PATH"
else
  echo "Warning: Virtual environment not found at $VENV_PATH. Using system python." >&2
fi

# Run the MCP server module directly using the activated python
python -m enforcer.mcp_server 