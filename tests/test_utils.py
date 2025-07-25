import subprocess
from unittest.mock import Mock, patch

import pytest

from enforcer.utils import get_git_modified_files, run_command, get_git_root


def test_get_git_modified_files_modified():
    with patch("enforcer.utils.run_command") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess(["git", "rev-parse", "--is-inside-work-tree"], 0, "true\n"),
            subprocess.CompletedProcess(["git", "status", "--porcelain"], 0, " M file1.py\nA  file2.py\n?? file3.py\n"),
        ]
        assert get_git_modified_files() == ["file1.py", "file2.py", "file3.py"]


def test_get_git_modified_files_no_repo():
    with patch("enforcer.utils.run_command") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            128, ["git", "rev-parse", "--is-inside-work-tree"], stderr="Not a git repository"
        )
        assert get_git_modified_files() == []


def test_get_git_modified_files_empty():
    with patch("enforcer.utils.run_command") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess(["git", "rev-parse", "--is-inside-work-tree"], 0, "true\n"),
            subprocess.CompletedProcess(["git", "status", "--porcelain"], 0, ""),
        ]
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


def test_get_git_root():
    with patch("enforcer.utils.run_command") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="/root\n")
        assert get_git_root() == "/root"

def test_get_git_root_not_repo():
    with patch("enforcer.utils.run_command") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(128, ["git"], stderr="not a repo")
        assert get_git_root() is None

def test_get_git_root_timeout():
    with patch("enforcer.utils.run_command") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(["git"], 5)
        assert get_git_root() is None

def test_run_command_file_not_found():
    with pytest.raises(FileNotFoundError):
        run_command(["missing_cmd"])

def test_run_command_called_process_error():
    with patch("subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.communicate.return_value = ("out", "err")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        with pytest.raises(subprocess.CalledProcessError):
            run_command(["cmd"], check=True)
