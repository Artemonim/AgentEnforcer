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
