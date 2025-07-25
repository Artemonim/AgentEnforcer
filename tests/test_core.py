from unittest.mock import MagicMock, patch

import pytest

from enforcer.core import Enforcer


@pytest.fixture
def enforcer(tmp_path):
    return Enforcer(str(tmp_path))


def test_scan_files_non_existent(enforcer):
    enforcer.target_paths = ["nonexistent"]
    files_by_lang, messages = enforcer.scan_files()
    assert not files_by_lang
    assert messages == ["Path does not exist: nonexistent"]


def test_scan_files_single_file(enforcer, tmp_path):
    file = tmp_path / "test.py"
    file.write_text("code")
    enforcer.target_paths = [str(file)]
    with patch.object(enforcer, "get_language", return_value="python"):
        files_by_lang, messages = enforcer.scan_files()
        assert files_by_lang == {"python": [str(file)]}
        assert not messages


def test_scan_files_directory(enforcer, tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file = subdir / "test.py"
    file.write_text("code")
    enforcer.target_paths = [str(tmp_path)]
    with patch.object(enforcer, "get_language", return_value="python"):
        files_by_lang, messages = enforcer.scan_files()
        assert files_by_lang == {"python": [str(file)]}
        assert not messages


def test_scan_files_gitignore(enforcer, tmp_path):
    file = tmp_path / "ignored.py"
    file.write_text("code")
    enforcer.target_paths = [str(file)]
    enforcer.gitignore = lambda p: True
    files_by_lang, messages = enforcer.scan_files()
    assert not files_by_lang
    assert not messages


def test_scan_files_no_language(enforcer, tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("text")
    enforcer.target_paths = [str(file)]
    with patch.object(enforcer, "get_language", return_value=None):
        files_by_lang, messages = enforcer.scan_files()
        assert not files_by_lang
        assert messages == [f"No supported language for file: {str(file)}"]


def test_run_checks_structured(tmp_path):
    enforcer = Enforcer(str(tmp_path))
    with patch.object(enforcer, "scan_files", return_value=({}, ["No files"])):
        result = enforcer.run_checks_structured()
        assert result["messages"] == ["No files"]
    with patch.object(
        enforcer,
        "scan_files",
        return_value=({"python": [str(tmp_path / "test.py")]}, []),
    ):
        mock_plugin = MagicMock()
        mock_plugin.autofix_style.return_value = {"changed_count": 0}
        mock_plugin.lint.return_value = {"errors": [], "warnings": []}
        with patch.object(enforcer, "plugins", {"python": mock_plugin}):
            with patch.object(enforcer, "check_tools", return_value=True):
                result = enforcer.run_checks_structured()
                assert result["errors"] == []
                assert result["warnings"] == []
                assert result["formatted_files"] == 0


def test_check_tools(tmp_path):
    enforcer = Enforcer(str(tmp_path))
    mock_plugin = MagicMock()
    mock_plugin.get_required_commands.return_value = ["python"]
    assert enforcer.check_tools(mock_plugin)
    mock_plugin.get_required_commands.return_value = ["nonexistent"]
    assert not enforcer.check_tools(mock_plugin)


def test_run_checks_structured_with_issues(tmp_path):
    with patch("enforcer.core.load_plugins") as mock_load:
        mock_plugin = MagicMock()
        mock_plugin.language = "python"
        mock_plugin.autofix_style.return_value = {"changed_count": 1}
        mock_plugin.lint.return_value = {
            "errors": [{"file": "f.py", "message": "err"}],
            "warnings": [{"file": "f.py", "message": "warn"}],
        }
        mock_load.return_value = {"python": mock_plugin}
        enforcer = Enforcer(str(tmp_path))
        with patch.object(
            enforcer, "scan_files", return_value=({"python": ["file.py"]}, [])
        ):
            with patch.object(enforcer, "check_tools", return_value=True):
                result = enforcer.run_checks_structured()
                assert len(result["errors"]) == 1
                assert len(result["warnings"]) == 1
                assert result["formatted_files"] == 1
