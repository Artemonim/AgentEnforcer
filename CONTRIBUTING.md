# Contributing to Agent Enforcer

Thank you for your interest in contributing to Agent Enforcer! We welcome contributions of all kinds—bug reports, feature requests, documentation improvements, and code patches.

## How to Contribute

1. Fork the repository on GitHub.
2. Clone your fork with submodules:
    ```bash
    git clone --recursive https://github.com/your-username/AgentEnforcer.git
    cd AgentEnforcer
    ```
3. Create a feature branch:
    ```bash
    git checkout -b my-feature-branch
    ```
4. Make your changes on the feature branch.
5. Ensure all tests pass:
    ```bash
    pip install -e .[dev]
    pytest
    ```
6. Commit your changes and push to your fork:
    ```bash
    git commit -m "[MyFeature] Brief description"
    git push origin my-feature-branch
    ```
7. Open a Pull Request against the `master` branch of the main repository.

## Coding Guidelines

-   Follow the project’s existing style conventions.
-   Write clear, declarative comments and docstrings.
-   Include tests for new functionality in the `tests/` directory.
-   Update `CHANGELOG.md` with a summary of your changes under `## [NextRelease]`.

## Reporting Issues

If you encounter a bug or have a feature request, please open an issue on GitHub with:

-   A clear title and description.
-   Steps to reproduce (for bugs).
-   Expected vs. actual behavior.

## Code Review Process

-   PRs should be reviewed by at least one maintainer.
-   Address review comments promptly.

## Working with Submodules

### Updating the MCP Specification

To update the Model Context Protocol specification to the latest version:

```bash
# Update the submodule to the latest commit
git submodule update --remote Doc/modelcontextprotocol

# Commit the submodule update
git add Doc/modelcontextprotocol
git commit -m "Update MCP specification to latest version"
```

### If Submodules Are Missing

If you encounter issues with missing submodules:

```bash
# Initialize and update all submodules
git submodule update --init --recursive

# Or update a specific submodule
git submodule update --init Doc/modelcontextprotocol
```

---

Thank you for making Agent Enforcer better!
