import subprocess
from unittest.mock import patch

import pytest

from enforcer.plugins.js_ts import Plugin


def test_get_required_commands():
    plugin = Plugin()
    assert plugin.get_required_commands() == ["npx"]


def test_autofix_style(tmp_path):
    file = tmp_path / "test.js"
    file.write_text("console.log ( 'hello' )")
    plugin = Plugin()
    with patch("enforcer.plugins.js_ts.run_command") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stderr="formatted " + str(file)),
            subprocess.CompletedProcess([], 0, stderr="fixed " + str(file)),
        ]
        result = plugin.autofix_style([str(file)])
        assert result["changed_count"] == 0  # Adjust based on actual


def test_lint(tmp_path):
    file = tmp_path / "test.js"
    file.write_text("console.log('hello')")
    plugin = Plugin()
    with patch("enforcer.plugins.js_ts.run_command") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, f"{file}:1:1 error test error"),
            subprocess.CompletedProcess([], 0, f"{file}:1: warning test warn"),
        ]
        result = plugin.lint([str(file)], [])
        assert len(result["errors"]) > 0


def test_lint_config_error(tmp_path):
    file = tmp_path / "test.js"
    file.write_text("code")
    plugin = Plugin()
    with patch("enforcer.plugins.js_ts.run_command") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            [], 1, stdout="", stderr="config error"
        )
        result = plugin.lint([str(file)], [])
        assert len(result["errors"]) == 1
        assert "config error" in result["errors"][0]["message"]


def test_lint_parse_error(tmp_path):
    file = tmp_path / "test.js"
    file.write_text("code")
    plugin = Plugin()
    with patch("enforcer.plugins.js_ts.run_command") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            [], 0, stdout="invalid json"
        )
        result = plugin.lint([str(file)], [])
        assert len(result["errors"]) == 1
        assert "Failed to parse" in result["errors"][0]["message"]


def test_lint_timeout(tmp_path):
    file = tmp_path / "test.js"
    file.write_text("code")
    plugin = Plugin()
    with patch("enforcer.plugins.js_ts.run_command") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(["cmd"], 10)
        result = plugin.lint([str(file)], [])
        assert len(result["errors"]) == 1
        assert "timed out" in result["errors"][0]["message"]


def test_compile():
    plugin = Plugin()
    with patch("enforcer.plugins.js_ts.run_command") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            [], 1, stdout="error1\nerror2"
        )
        errors = plugin.compile(["file.js"])
        assert errors == ["error1", "error2"]


def test_compile_timeout():
    plugin = Plugin()
    with patch("enforcer.plugins.js_ts.run_command") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(["cmd"], 10)
        errors = plugin.compile(["file.js"])
        assert errors == ["TSC command timed out or was not found."]


def test_test():
    plugin = Plugin()
    with patch("enforcer.plugins.js_ts.run_command") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["cmd"], output="test error"
        )
        errors = plugin.test("root")
        assert errors == ["test error"]


def test_test_timeout():
    plugin = Plugin()
    with patch("enforcer.plugins.js_ts.run_command") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(["cmd"], 10)
        errors = plugin.test("root")
        assert errors == ["Jest command timed out or was not found."]
