import subprocess
import pytest
from unittest.mock import patch
from enforcer.plugins.python import Plugin
import json

def test_get_required_commands():
    plugin = Plugin()
    assert plugin.get_required_commands() == ["python"]
def test_autofix_style(tmp_path):
    file = tmp_path / "test.py"
    file.write_text("def f( ):pass")
    plugin = Plugin()
    with patch("enforcer.plugins.python.run_command") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stderr="reformatted " + str(file)),
            subprocess.CompletedProcess([], 0, stderr="Fixing " + str(file)),
        ]
        result = plugin.autofix_style([str(file)])
        assert result["changed_count"] == 1
def test_lint(tmp_path):
    file = tmp_path / "test.py"
    file.write_text("print('hello')")
    plugin = Plugin()
    with patch("enforcer.plugins.python.run_command") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, json.dumps({"generalDiagnostics": [{"file": str(file), "range": {"start": {"line": 0}}, "message": "error msg", "rule": "rule1", "severity": "error"}]})),
            subprocess.CompletedProcess([], 0, f"{file}:1:1 E001 test error"),
            subprocess.CompletedProcess([], 0, f"{file}:1: error: test mypy error [mypy1]"),
        ]
        result = plugin.lint([str(file)], [])
        assert len(result["errors"]) > 0
        assert "pyright" in result["errors"][0]["tool"] 