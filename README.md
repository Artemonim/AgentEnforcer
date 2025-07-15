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

### 2. Configure in Cursor

Once installed, you need to tell Cursor how to run the MCP server. We provide helper scripts for both Windows (`run_mcp.bat`) and Unix-based systems (`run_mcp.sh`).

1.  Go to `File > Settings > Cursor` (or `Code > Settings > Settings`, then find `Cursor` in the list).
2.  Scroll down to the **MCP** section.
3.  Click **"Open mcp.json"**.
4.  Add the following configuration to the `mcpServers` object. **Important:** You must use the **absolute path** to the correct script for your operating system.

    ```json
    {
        "mcpServers": {
            "agent_enforcer": {
                "command": "path/to/your/AgentEnforcer/run_mcp.bat_or_sh",
                "args": []
            }
        }
    }
    ```

    -   On **Windows**, set the `command` to the absolute path of `run_mcp.bat`.
    -   On **macOS/Linux**, set the `command` to the absolute path of `run_mcp.sh`.

    **How to get the absolute path:**

    -   In the Cursor file explorer, right-click on the appropriate script (`run_mcp.bat` or `run_mcp.sh`) and choose `Copy Path`.
    -   Paste the path into the `command` field.
    -   **Crucially**, ensure all backslashes (`\`) are replaced with forward slashes (`/`).

5.  Save the `mcp.json` file.
6.  **Restart Cursor** to ensure it picks up the new configuration.

After configuration, the `run_check` tool will be available to the AI Agent in Cursor.

### Troubleshooting

-   **macOS/Linux users:** Make sure `run_mcp.sh` is executable. Run `chmod +x run_mcp.sh` in your terminal.
-   Ensure the absolute path in `mcp.json` is correct and uses forward slashes.
-   Check that your `venv` is set up correctly and has the dependencies from `pip install -e .` installed.
-   If the tool still doesn't appear, check the logs. On Windows, Cursor may open a command prompt window showing script output/errors.

## Using the MCP Tool

The server exposes one primary tool: `run_check`.

#### Tool: `run_check`

Runs a quality check on the codebase. It can be targeted to specific files or directories.

**Parameters:**

-   `targets` (Optional, `list[str]`): A list of file or directory paths to check. If omitted, the entire repository is checked.
-   `check_git_modified_files` (Optional, `bool`, default: `false`): If set to `true`, the tool will ignore the `targets` parameter and instead check only the files that have been modified, added, or renamed according to `git status`. This is extremely useful for checking only the changes made in the current session.
-   `verbose` (Optional, `bool`, default: `false`): If `true`, the output will be a detailed list of every issue. For AI use, it is better to leave this False unless a detailed report is explicitly needed.

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
