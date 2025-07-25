import subprocess
import pytest
from unittest.mock import patch
from enforcer.plugins.csharp import Plugin
def test_get_required_commands():
    plugin = Plugin()
    assert "dotnet" in plugin.get_required_commands()
def test_autofix_style(tmp_path):
    file = tmp_path / "test.cs"
    file.write_text("class C { }")
    plugin = Plugin()
    with patch("enforcer.plugins.csharp.run_command") as mock_run:
        mock_run.side_effect = [subprocess.CompletedProcess([], 0, "formatted")]
        result = plugin.autofix_style([str(file)])
        assert "changed_count" in result
def test_lint(tmp_path):
    file = tmp_path / "test.cs"
    file.write_text("class C {}")
    plugin = Plugin()
    with patch("enforcer.plugins.csharp.run_command") as mock_run:
        mock_run.side_effect = [subprocess.CompletedProcess([], 0, stdout=f"{file}(1,1): error CS0001: test error", stderr="")]
        result = plugin.lint([str(file)], [])
        assert len(result["errors"]) > 0 