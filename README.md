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

## MCP-Tool Integration (Cursor IDE)

You can use Agent Enforcer directly within Cursor IDE as a custom tool.

### 1. Install/Update Agent Enforcer

First, ensure you have the latest version installed in your environment. If you are developing locally in this repository, run:

```bash
pip install -e .
```

This command makes the `agent-enforcer-mcp` script available.

### 2. Add as an MCP Server in Cursor

1.  Go to `File > Settings > Cursor`.
2.  Scroll down to the `Model Context Protocol (MCP)` section.
3.  Click `+ Add New MCP Server`.
4.  Fill in the details:

    -   **Name**: `agent-enforcer` (or any name you prefer)
    -   **Type**: `stdio`
    -   **Command**: `agent-enforcer-mcp`

    _Note: If you are using a virtual environment (like venv or conda), you might need to provide the full path to the script, e.g., `C:\path\to\your\venv\Scripts\agent-enforcer-mcp.exe` on Windows or `~/path/to/your/venv/bin/agent-enforcer-mcp` on macOS/Linux._

5.  Click `Add`.

### 3. Usage in Cursor

Now you can ask the Cursor AI to use the tool. For example:

> Run a quality check on the `enforcer/core.py` file using the agent-enforcer tool.

The AI will find and execute the `run_check` tool, providing the results directly in the chat.

The server exposes one primary tool: `run_check`.

#### Tool: `run_check`

Runs a quality check on the codebase. It can be targeted to specific files or directories.

**Parameters:**

-   `targets` (Optional, `list[str]`): A list of file or directory paths to check. If omitted, the entire repository is checked.
-   `check_git_modified_files` (Optional, `bool`, default: `false`): If set to `true`, the tool will ignore the `targets` parameter and instead check only the files that have been modified, added, or renamed according to `git status`. This is extremely useful for checking only the changes made in the current session.
-   `verbose` (Optional, `bool`, default: `false`): If `true`, the output will be a detailed list of every issue. If `false`, the output will be a more concise summary grouped by file.

**Returns:**

-   `str`: A formatted string containing the results of the check, similar to what you would see in the console.

**Example Usage (for an AI Agent):**

-   **Check the whole project:**
    ```json
    {
        "tool": "run_check"
    }
    ```
-   **Check a specific file and directory:**
    ```json
    {
        "tool": "run_check",
        "targets": ["src/main.py", "src/utils/"]
    }
    ```
-   **Check only the files I've changed:**
    ```json
    {
        "tool": "run_check",
        "check_git_modified_files": true
    }
    ```
-   **Get a detailed list of issues for a specific file:**
    ```json
    {
        "tool": "run_check",
        "targets": ["src/problematic_file.py"],
        "verbose": true
    }
    ```

This setup allows an AI agent to flexibly run checks on the entire codebase, specific parts of it, or just the work in progress, making it a much more efficient and targeted tool.
