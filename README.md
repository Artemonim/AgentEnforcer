# Agent Enforcer

## Development Setup

### Git Submodules

This project includes the Model Context Protocol (MCP) specification as a git submodule:

```bash
# Clone the repository with submodules
git clone --recursive https://github.com/your-username/AgentEnforcer.git

# Or if already cloned, initialize and update submodules
git submodule update --init --recursive
```

The MCP specification is located in `Doc/modelcontextprotocol/` and contains the official protocol documentation and examples.

## Installation Options

### Option 1: Global Installation (Recommended for MCP)

Install once system-wide and use across all projects:

```bash
pip install agent-enforcer
```

**MCP Configuration for global install:**

-   **Windows**: `"command": "agent-enforcer-mcp.exe"`
-   **macOS/Linux**: `"command": "agent-enforcer-mcp"`

### Option 2: Local Development Installation

Install in project-specific virtual environment:

```bash
pip install -e .
```

**MCP Configuration for local install:**

-   **Windows**: `"command": "./venv/Scripts/agent-enforcer-mcp.exe"`
-   **macOS/Linux**: `"command": "./venv/bin/agent-enforcer-mcp"`

### Option 3: Standalone Installation

Install in dedicated location and use across projects:

```bash
# Create dedicated environment
python -m venv ~/tools/agent-enforcer-env
source ~/tools/agent-enforcer-env/bin/activate  # Linux/macOS
# or
~/tools/agent-enforcer-env/Scripts/activate     # Windows

pip install agent-enforcer

# Add to PATH or use full path in MCP config
```

**MCP Configuration for standalone:**

-   **Windows**: `"command": "C:/Users/YourUser/tools/agent-enforcer-env/Scripts/agent-enforcer-mcp.exe"`
-   **macOS**: `"command": "/Users/YourUser/tools/agent-enforcer-env/bin/agent-enforcer-mcp"`
-   **Linux**: `"command": "/home/YourUser/tools/agent-enforcer-env/bin/agent-enforcer-mcp"`

## Usage

```bash
agent-enforcer [path]  # Checks current directory if no path
agent-enforcer src/game.py  # Check single file
agent-enforcer src  # Check directory
```

## Configuration

-   The tool creates `.enforcer/config.json` in your project root upon first run.
-   **Debug Mode**: To enable the `debug` parameter for the `checker` tool, edit this file and set `"debug_mode_enabled": true`. This is useful for tool development.
-   **Rule Management**: You can disable specific linting rules by adding them to the `disabled_rules` section.
-   **Tool-Specific Configs**: For more advanced configurations, you can add tool-specific files like `.enforcer/flake8.json`.

## MCP-Tool Integration (Cursor IDE)

You can use Agent Enforcer directly within Cursor IDE as a custom tool.

### 1. Choose Your Installation Method

**For most users, global installation (Option 1) is recommended** as it allows you to use Agent Enforcer across all projects without reinstalling.

### 2. Configure in Cursor

Once installed, you need to tell Cursor how to run the MCP server.

1.  Go to `File > Settings > Cursor` (or `Code > Settings > Settings`, then find `Cursor` in the list).
2.  Scroll down to the **MCP** section.
3.  Click **"Open mcp.json"**.
4.  Add the appropriate configuration based on your installation method:

#### Global Installation (Recommended)

```json
{
    "mcpServers": {
        "agent_enforcer": {
            "command": "agent-enforcer-mcp"
        }
    }
}
```

#### Local Virtual Environment

```json
{
    "mcpServers": {
        "agent_enforcer": {
            "command": "./venv/Scripts/agent-enforcer-mcp.exe"
        }
    }
}
```

#### Using run_mcp Scripts (Cross-platform)

```json
{
    "mcpServers": {
        "agent_enforcer": {
            "command": "./run_mcp.bat"
        }
    }
}
```

**Platform-specific notes:**

-   **Windows**: Use `.exe` suffix for executables, forward slashes in paths
-   **macOS/Linux**: Use `run_mcp.sh` instead of `run_mcp.bat`
-   **macOS/Linux users**: Make sure `run_mcp.sh` is executable: `chmod +x run_mcp.sh`

5.  Save the `mcp.json` file.

After configuration, the `checker` tool will be available to the AI Agent in Cursor.

## Available Tools and Prompts

### Tools

#### `checker`

The main tool that runs comprehensive code quality checks using multiple linters:

-   **black** - Code formatting
-   **isort** - Import sorting
-   **flake8** - Style guide enforcement
-   **mypy** - Static type checking
-   **pyright** - Type checking and analysis

**Parameters:**

-   `resource_uris` - List of file URIs to check (optional)
-   `check_git_modified_files` - Check only modified files in git (default: false)
-   `verbose` - Provide detailed output (default: false)
-   `timeout_seconds` - Timeout for the check (default: 0 = no timeout)
-   `root` - Repository root path (auto-detected if not provided)

### Prompts (MCP Protocol)

The server also provides three prompts for structured AI interactions:

#### `fix-this-file`

**Title:** Fix Code Issues  
**Description:** Generates a structured prompt asking the AI to fix specific linting issues in a given file.

#### `summarize-lint-errors`

**Title:** Summarize Lint Errors  
**Description:** Creates a prompt asking the AI to summarize and prioritize the most critical errors from a lint report.

#### `explain-rule`

**Title:** Explain Lint Rule  
**Description:** Generates a prompt asking the AI to explain a specific linting rule and provide examples of how to fix violations.

**Note:** Prompts are part of the MCP protocol but are **not currently supported in Cursor**. They work in other MCP-compatible clients that support the prompts API.

### Installation Best Practices

**When to use each method:**

-   **Global install**: The best choice for MCP, as it works in all projects without additional configuration.
-   **Local install**: If you want to explicitly set Agent Enforcer as dev dependency.
-   **Standalone**: It is good for isolated installation in a system without polluting global Python.

**Recommendations for end users:**

-   Use **global installation** for MCP - this is the easiest and most reliable way
-   Use `pip install -e` for development and debugging of Enforcer.

### Troubleshooting

-   **Command not found**: Make sure that the Python Scripts directory is added to the PATH for global installation
-   **Permission errors**: On macOS/Linux, use `chmod +x` for scripts
-   **Virtual environment issues**: Activate the virtual environment before launching
-   If the tool doesn't appear in Cursor, check the logs (View > Output > Cursor MCP).
-   **Path issues**: Use forward slashes (`/`) in paths, even on Windows
