import subprocess
from unittest.mock import Mock, patch

import pytest

from enforcer.utils import get_git_modified_files, run_command


@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock:
        yield mock


def test_get_git_modified_files_modified(mock_subprocess_run):
    mock_subprocess_run.side_effect = [
        Mock(returncode=0),  # rev-parse
        Mock(returncode=0, stdout=" M file1.py\nA  file2.py\n?? file3.py\n"),
    ]
    assert get_git_modified_files() == ["file1.py", "file2.py", "file3.py"]


def test_get_git_modified_files_no_repo(mock_subprocess_run):
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        128, ["git"], stderr="Not a git repository"
    )
    assert get_git_modified_files() == []


def test_get_git_modified_files_empty():
    with patch("subprocess.run") as mock:
        mock.side_effect = [Mock(returncode=0), Mock(returncode=0, stdout="")]
        assert get_git_modified_files() == []


def test_run_command_success():
    with patch("subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.communicate.return_value = ("out", "err")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        result = run_command(["echo", "test"])
        assert result.returncode == 0


def test_run_command_timeout():
    with patch("subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(["cmd"], 10)
        mock_popen.return_value = mock_process
        with pytest.raises(subprocess.TimeoutExpired):
            run_command(["sleep", "20"], timeout=10)
