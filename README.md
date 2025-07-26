<!-- ain badges -->

[![PyPI version](https://badge.fury.io/py/agent-enforcer.svg)](https://badge.fury.io/py/agent-enforcer)
[![Python versions](https://img.shields.io/pypi/pyversions/agent-enforcer.svg)](https://pypi.org/project/agent-enforcer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![GitHub stars](https://img.shields.io/github/stars/Artemonim/AgentEnforcer.svg?style=social&label=Star)](https://github.com/Artemonim/AgentEnforcer)
[![GitHub forks](https://img.shields.io/github/forks/Artemonim/AgentEnforcer.svg?style=social&label=Fork)](https://github.com/Artemonim/AgentEnforcer)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Typed with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![codecov](https://codecov.io/gh/Artemonim/AgentEnforcer/branch/master/graph/badge.svg)](https://codecov.io/gh/Artemonim/AgentEnforcer)

# Agent Enforcer: A Modular Code Quality Tool

**Agent Enforcer** is a powerful and flexible code quality checking tool designed to be used by both developers and AI agents. It integrates multiple linters and formatters to provide comprehensive feedback, and it can be used as a standalone CLI tool or as an MCP server within compatible editors like Cursor.

---

## Table of Contents

-   [Features](#features)
-   [Installation](#installation)
-   [Usage](#usage)
-   [Configuration](#configuration)
-   [MCP Integration (Cursor IDE)](#mcp-integration-cursor-ide)
    -   [Tool: `checker`](#tool-checker)
    -   [Prompts](#prompts)
-   [Logging](#logging)
-   [Sponsorship](#support-the-project)
-   [Contributing](#contributing)
-   [Development Setup](#development-setup)
-   [Changelog](#changelog)
-   [License](#license)

---

## Features

-   **Flexible CLI**: Check specific files/directories, or only files modified in git.
-   **Smart File Discovery**: Automatically respects `.gitignore` and excludes common test fixture/submodule directories by default.
-   **Dynamic Configuration**: Uses a project-local `.enforcer/config.json` that is reloaded on every check, so no server restart is needed.
-   **MCP Server**: Exposes its functionality as a `checker` tool for AI agents in editors like Cursor.
-   **Robust and Loggable**: Executes external tools safely with timeouts and generates detailed logs for diagnostics.
-   **Supported Languages**: Python, C#, Kotlin, JavaScript, TypeScript

## Installation

The recommended installation method depends on your use case.

### Option 1: As a User (Global or Virtual Environment)

This is the standard way to use the tool in your projects.

**A) Global Installation:**
Install it once system-wide. This is the easiest method for MCP integration.

```bash
pip install agent-enforcer
```

**B) Project-specific Installation:**
Install it as a dependency in your project's virtual environment.

```bash
# In your activated virtual environment
pip install agent-enforcer
```

### Option 2: As a Developer (From Source)

If you want to contribute to Agent Enforcer itself, clone the repository and install it in editable mode.

```bash
# Clone the repository
git clone --recursive https://github.com/Artemonim/AgentEnforcer.git
cd AgentEnforcer

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# venv\Scripts\activate  # On Windows

# Install in editable mode with development dependencies
pip install -e .[dev]
```

## Usage

You can run Agent Enforcer from your terminal to check a path. If no path is provided, it checks the current directory.

```bash
# Check the current directory
agent-enforcer

# Check a specific file
agent-enforcer src/game.py

# Check a whole directory
agent-enforcer src/
```

For more advanced CLI options, use `agent-enforcer-cli --help`.

## Configuration

On its first run, the tool creates a `.enforcer/config.json` file in your project root. You can modify this file to customize behavior. Changes are applied immediately on the next check.

-   `debug_mode_enabled` (boolean, default: `false`): Enables Enforcer dev-output.
-   `check_fixtures` (boolean, default: `false`): Includes test fixture files in checks.
-   `check_submodules` (boolean, default: `false`): Includes git submodules in checks.
-   `disabled_rules` (object): Disables specific linter rules (e.g., `{"python": ["E501"]}`).
-   `custom_fixture_patterns` (object): Defines custom patterns for fixture detection.

## MCP Integration (Cursor IDE)

To use Agent Enforcer within Cursor, you need to configure the MCP server.

1.  Go to `File > Settings > Cursor`.
2.  Scroll to the **MCP** section and click **"Open mcp.json"**.
3.  Add a configuration based on your installation method.

#### For Global Installation (Recommended)

```json
{
    "mcpServers": {
        "agent_enforcer": {
            "command": "agent-enforcer-mcp"
        }
    }
}
```

#### For Local/Development Installation

If you installed the package locally in a virtual environment, you must provide the full path to the executable.

-   **Windows:**

```json
{
    "mcpServers": {
        "agent_enforcer": {
            "command": "./venv/Scripts/agent-enforcer-mcp.exe"
        }
    }
}
```

-   **macOS/Linux:**

```json
{
    "mcpServers": {
        "agent_enforcer": {
            "command": "./venv/bin/agent-enforcer-mcp"
        }
    }
}
```

### Tool: `checker`

The main tool that runs comprehensive code quality checks.

**Parameters:**

-   `resource_uris` (list[str], optional): File URIs to check.
-   `check_git_modified_files` (bool, default: `false`): Check only modified files.
-   `verbose` (bool, default: `false`): Provide detailed, per-file output.
-   `timeout_seconds` (int, default: `0`): Timeout for the check (0 = no timeout).
-   `root` (str, optional): Repository root path (usually auto-detected).
-   `debug` (bool, default: `false`): Enable extra-verbose debug logging (must also be enabled in `config.json`).

### Prompts

The server provides three prompts for structured AI interactions.

-   **`fix-this-file`**: Generates a prompt asking the AI to fix specific linting issues in a file.
-   **`summarize-lint-errors`**: Creates a prompt for the AI to summarize and prioritize critical errors.
-   **`explain-rule`**: Generates a prompt for the AI to explain a specific linting rule.

**Note:** Prompts are part of the MCP protocol but are **not currently supported in Cursor**. They may work in other MCP-compatible clients that support the prompts API.

## Logging

Agent Enforcer generates two log files inside the `.enforcer/` directory in your project root, which can be useful for diagnostics and analysis.

-   **`Enforcer_last_check.log`**: A machine-readable JSON log containing detailed information about all issues found during the last check. This is useful for integrations or for tools that need to programmatically access the results.
-   **`Enforcer_stats.log`**: A historical log that tracks the frequency of each violated rule over time. Analyzing this file can help identify recurring problems in a codebase, which can inform decisions about custom rule configurations or prompt-engineering problems.

It is recommended to add this logs to your project's `.gitignore` file to avoid committing these logs and local configuration to version control.

```gitignore
# Agent Enforcer logs
.enforcer/Enforcer_last_check.log
.enforcer/Enforcer_stats.log
```

## Support the Project

Agent Docstrings is an independent open-source project. If you find this tool useful and want to support its ongoing development, your help would be greatly appreciated.

Here are a few ways you can contribute:

-   **Give a Star:** The simplest way to show your support is to star the project on [GitHub](https://github.com/Artemonim/AgentDocstrings)! It increases the project's visibility.
-   **Support My Work:** Your financial contribution helps me dedicate more time to improving this tool and creating other open-source projects. On my [**Boosty page**](https://boosty.to/artemonim), you can:
    -   Make a **one-time donation** to thank me for this specific project.
    -   Become a **monthly supporter** to help all of my creative endeavors.
-   **Try a Recommended Tool:** This project was inspired by my work with LLMs. If you're looking for a great service to work with multiple neural networks, check out [**Syntx AI**](https://t.me/syntxaibot?start=aff_157453205). Using my referral link is another way to support my work at no extra cost to you.

Thank you for your support!

## Contributing

We welcome contributions! Please see our [**CONTRIBUTING.md**](CONTRIBUTING.md) for detailed instructions on how to get started, our development workflow, and coding standards.

## Development Setup

The project includes the Model Context Protocol (MCP) specification as a git submodule. Make sure you clone it correctly if you plan to contribute.

```bash
# When cloning for the first time
git clone --recursive https://github.com/Artemonim/AgentEnforcer.git

# Or if you have already cloned it without submodules
git submodule update --init --recursive
```

The MCP specification is located in `Doc/modelcontextprotocol/`.

## Changelog

See [**CHANGELOG.md**](CHANGELOG.md) for a list of changes and version history.

## License

This project is licensed under the MIT License. See the [**LICENSE**](LICENSE) file for details.
