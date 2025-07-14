@echo off
REM This script ensures that the MCP server is run with the correct python executable
REM from the user's current environment on Windows.

REM Get the directory of this script. %~dp0 expands to the drive and path of the script.
set "SCRIPT_DIR=%~dp0"

REM Define the path to the venv activation script for Windows
set "VENV_PATH=%SCRIPT_DIR%venv\Scripts\activate.bat"

IF EXIST "%VENV_PATH%" (
    echo "Activating virtual environment..."
    call "%VENV_PATH%"
) ELSE (
    echo "Warning: Virtual environment not found at %VENV_PATH%. Using system python."
)

echo "Starting MCP server..."
REM Run the MCP server module directly using the (potentially venv) python
python -m enforcer.mcp_server 