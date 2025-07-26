# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [NextRelease]

### Header

-   **subtitle**: describtion

## [0.9.0] - 2025-06-26

### Added

-   **Initial Release**: First public beta of Agent Enforcer, a modular code quality tool.
-   **Python Support**: Integrated tools (`black`, `isort`, `flake8`, `mypy`, `pyright`) for comprehensive Python code analysis.
-   **MCP Server**: Packaged as a FastMCP tool for use in editors like Cursor, exposing a `checker` function.
-   **Powerful CLI**:
    -   Check specific paths or only git-modified files (`--modified`).
    -   Manage rules (`--ignore`, `--blacklist`) and severities (`--error`, `--warning`) from the command line.
-   **Smart File Discovery**:
    -   Automatically respects `.gitignore`.
    -   Excludes common test fixtures and git submodules by default.
-   **Dynamic Configuration**:
    -   Uses a project-local `.enforcer/config.json` for settings.
    -   Configuration is reloaded on each check without restarting the server.
    -   Supports toggling fixture/submodule checks and disabling rules.
-   **Robustness and Logging**:
    -   Safe execution of external tools with timeouts.
    -   Generates a detailed `Enforcer_last_check.log` for diagnostics.
