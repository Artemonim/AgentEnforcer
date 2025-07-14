# Agent Enforcer

## Installation

For global installation (once published):

```bash
pip install agent-enforcer
```

For local development in this repo:

```bash
pip install -e .
```

## Usage

```bash
agent-enforcer [path]  # Checks current directory if no path
agent-enforcer src/game.py  # Check single file
agent-enforcer src  # Check directory
```

## Configuration

-   The tool creates `.enforcer/config.json` for disabled rules (blacklist).
-   Add tool-specific configs like `.enforcer/flake8.json` for full rule sets, which can be edited.
-   Use --ignore flag for temporary disables, e.g., --ignore E501 or python:E501.

## Adding Plugins

Create a new file in enforcer/plugins/ with a Plugin class defining language, extensions, and check methods.

# Remember to replace placeholders like YOUR_NAME.
