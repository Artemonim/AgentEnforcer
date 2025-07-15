from setuptools import find_packages, setup

setup(
    name="agent-enforcer",
    version="0.3.0",
    description="Agent Enforcer: A modular code quality checking tool",
    author="YOUR_NAME",  # * Replace with actual author
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "gitignore-parser",
        "black",
        "isort",
        "flake8",
        "mypy",
        "pyright",
        "pytest",
        "fastmcp",
    ],
    entry_points={
        "console_scripts": [
            "agent-enforcer = enforcer.main:main",
            "agent-enforcer-mcp = enforcer.mcp_server:main",
        ],
    },
)
