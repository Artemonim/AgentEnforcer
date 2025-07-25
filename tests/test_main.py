import sys
from unittest.mock import MagicMock, patch

import pytest

from enforcer.main import main


def test_main_default(capsys):
    with patch("sys.argv", ["agent-enforcer"]), patch(
        "enforcer.main.load_config", return_value={}
    ), patch("enforcer.main.Enforcer") as mock_enforcer, patch(
        "enforcer.main.os.getcwd", return_value="/root"
    ):
        mock_instance = mock_enforcer.return_value
        mock_instance.run_checks.return_value = "Check output"
        main()
        captured = capsys.readouterr()
        assert "Check output" in captured.out
        mock_enforcer.assert_called_with("/root", ["."], {}, verbose=False)


def test_main_verbose(capsys):
    with patch("sys.argv", ["agent-enforcer", "--verbose"]), patch(
        "enforcer.main.load_config", return_value={}
    ), patch("enforcer.main.Enforcer") as mock_enforcer, patch(
        "enforcer.main.os.getcwd", return_value="/root"
    ):
        mock_instance = mock_enforcer.return_value
        mock_instance.run_checks.return_value = "Verbose output"
        main()
        captured = capsys.readouterr()
        assert "Verbose output" in captured.out
        mock_enforcer.assert_called_with("/root", ["."], {}, verbose=True)


def test_main_modified(capsys):
    with patch("sys.argv", ["agent-enforcer", "--modified"]), patch(
        "enforcer.main.load_config", return_value={}
    ), patch("enforcer.main.get_git_modified_files", return_value=["mod.py"]), patch(
        "enforcer.main.Enforcer"
    ) as mock_enforcer, patch(
        "enforcer.main.os.getcwd", return_value="/root"
    ):
        mock_instance = mock_enforcer.return_value
        mock_instance.run_checks.return_value = "Modified output"
        main()
        captured = capsys.readouterr()
        assert "Modified output" in captured.out
        mock_enforcer.assert_called_with("/root", ["mod.py"], {}, verbose=False)


def test_main_with_root(capsys):
    with patch("sys.argv", ["agent-enforcer", "--root", "/fake_root"]), patch(
        "enforcer.main.load_config", return_value={}
    ), patch("enforcer.main.Enforcer") as mock_enforcer, patch(
        "enforcer.main.os.chdir"
    ) as mock_chdir, patch(
        "enforcer.main.os.getcwd", return_value="/fake_root"
    ):
        mock_instance = mock_enforcer.return_value
        mock_instance.run_checks.return_value = "Output"
        main()
        mock_chdir.assert_called_with("/fake_root")
        captured = capsys.readouterr()
        assert "Output" in captured.out


def test_main_with_blacklist(capsys):
    with patch("sys.argv", ["agent-enforcer", "--blacklist", "rule1"]), patch(
        "enforcer.main.load_config", return_value={}
    ), patch("enforcer.main.save_config") as mock_save, patch("sys.exit") as mock_exit:
        main()
        assert mock_save.called
        mock_exit.assert_called_with(0)
        captured = capsys.readouterr()
        assert "Configuration updated." in captured.out


def test_main_with_error(capsys):
    with patch("sys.argv", ["agent-enforcer", "--error", "rule1"]), patch(
        "enforcer.main.load_config", return_value={}
    ), patch("enforcer.main.save_config") as mock_save, patch("sys.exit") as mock_exit:
        main()
        assert mock_save.called
        mock_exit.assert_called_with(0)
        captured = capsys.readouterr()
        assert "Configuration updated." in captured.out


def test_main_with_ignore(capsys):
    with patch("sys.argv", ["agent-enforcer", "--ignore", "rule1"]), patch(
        "enforcer.main.load_config", return_value={}
    ), patch("enforcer.main.Enforcer") as mock_enforcer, patch(
        "enforcer.main.os.getcwd", return_value="/root"
    ):
        mock_instance = mock_enforcer.return_value
        mock_instance.run_checks.return_value = "Output"
        main()
        config = mock_enforcer.call_args[0][2]
        assert "rule1" in config["disabled_rules"]["global"]
        captured = capsys.readouterr()
        assert "Output" in captured.out
