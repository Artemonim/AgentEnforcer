import subprocess
from unittest.mock import patch

import pytest

from enforcer.plugins.kotlin import Plugin


def test_get_required_commands():
    plugin = Plugin()
    assert "./gradlew" in plugin.get_required_commands()


def test_autofix_style(tmp_path):
    file = tmp_path / "test.kt"
    file.write_text("fun f() { }")
    plugin = Plugin()
    with patch("enforcer.plugins.kotlin.run_command") as mock_run:
        mock_run.side_effect = [subprocess.CompletedProcess([], 0, "formatted")]
        result = plugin.autofix_style([str(file)])
        assert "changed_count" in result


def test_lint(tmp_path):
    file = tmp_path / "test.kt"
    file.write_text("fun f() {}")
    plugin = Plugin()
    with patch("enforcer.plugins.kotlin.run_command") as mock_run, patch(
        "os.path.exists", return_value=True
    ):
        mock_run.side_effect = [
            subprocess.CompletedProcess(
                [], 0, stdout=f"{file}:1:1: some ktlint error", stderr=""
            ),
            subprocess.CompletedProcess(
                [], 0, stdout=f"{file}:2:2 - some-rule - some detekt error", stderr=""
            ),
        ]
        result = plugin.lint([str(file)], [], root_path=str(tmp_path))
        assert len(result["errors"]) == 2


def test_lint_ktlint_error(tmp_path):
    file = tmp_path / "test.kt"
    file.write_text("code")
    plugin = Plugin()
    with patch("enforcer.plugins.kotlin.run_command") as mock_run, patch(
        "os.path.exists", return_value=True
    ):
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=f"{file}:1:1: error msg"),
            subprocess.CompletedProcess([], 0, stdout=""),
        ]
        result = plugin.lint([str(file)], [], root_path=str(tmp_path))
        assert len(result["errors"]) == 1
        assert "error msg" in result["errors"][0]["message"]


def test_lint_detekt_timeout(tmp_path):
    file = tmp_path / "test.kt"
    file.write_text("code")
    plugin = Plugin()
    with patch("enforcer.plugins.kotlin.run_command") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, ""),
            subprocess.TimeoutExpired(["cmd"], 10),
        ]
        result = plugin.lint([str(file)], [])
        assert len(result["errors"]) == 1
        assert "detekt failed" in result["errors"][0]["message"]


def test_compile_fail():
    plugin = Plugin()
    with patch("enforcer.plugins.kotlin.run_command") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess([], 1, "")
        errors = plugin.compile(["file.kt"])
        assert len(errors) == 1
        assert "Build failed" in errors[0]["message"]


def test_compile_timeout():
    plugin = Plugin()
    with patch("enforcer.plugins.kotlin.run_command") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(["cmd"], 10)
        errors = plugin.compile(["file.kt"])
        assert len(errors) == 1
        assert "timed out" in errors[0]["message"]


def test_test_fail():
    plugin = Plugin()
    with patch("enforcer.plugins.kotlin.run_command") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess([], 1, "")
        errors = plugin.test("root")
        assert len(errors) == 1
        assert "Tests failed" in errors[0]["message"]


def test_test_timeout():
    plugin = Plugin()
    with patch("enforcer.plugins.kotlin.run_command") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(["cmd"], 10)
        errors = plugin.test("root")
        assert len(errors) == 1
        assert "timed out" in errors[0]["message"]
