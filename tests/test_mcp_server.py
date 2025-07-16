import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import platform
import os
import pytest
import unittest
from enforcer.mcp_server import AgentEnforcerMCP, check_code


@pytest.fixture
def mcp_server():
    return AgentEnforcerMCP()


class TestMcpServer(unittest.TestCase):

    def _run_test_case(self, test_name, params):
        """Helper to run a single test case."""
        with self.subTest(test_name):
            targets = params.get("targets")
            # The tool expects targets as a JSON string
            targets_str = json.dumps(targets) if targets is not None else "null"

            with patch("enforcer.mcp_server.subprocess.run") as mock_run, patch(
                "enforcer.mcp_server.get_git_modified_files"
            ) as mock_git_files:

                mock_git_files.return_value = ["modified_file.py"]
                mock_proc = MagicMock()
                mock_proc.returncode = 0
                mock_proc.stdout = "Check completed."
                mock_proc.stderr = ""
                mock_run.return_value = mock_proc

                check_code(
                    targets=targets_str,
                    check_git_modified_files=params["check_git_modified_files"],
                    verbose=params["verbose"],
                    timeout_seconds=params["timeout_seconds"],
                    debug=params["debug"],
                    # For testing purposes, we assume the root is the current dir
                    root=params.get("root", os.getcwd()),
                )

                if params["check_git_modified_files"]:
                    mock_git_files.assert_called_once()
                else:
                    # Check that subprocess.run was called
                    self.assertTrue(mock_run.called)
                    called_args, called_kwargs = mock_run.call_args

                    # Verify timeout is passed correctly
                    self.assertEqual(
                        called_kwargs.get("timeout"), params["timeout_seconds"]
                    )

                    # Verify targets are in the command
                    command = called_args[0]
                    if targets:
                        for target in targets:
                            self.assertIn(target, command)

    def test_all_cases(self):
        test_data = {
            "test_01_basic_no_targets": {
                "targets": None,
                "check_git_modified_files": False,
                "verbose": False,
                "timeout_seconds": 15,
                "debug": False,
            },
            "test_02_basic_no_targets_debug": {
                "targets": None,
                "check_git_modified_files": False,
                "verbose": False,
                "timeout_seconds": 90,
                "debug": True,
            },
            "test_03_git_modified_short_timeout": {
                "targets": None,
                "check_git_modified_files": True,
                "verbose": False,
                "timeout_seconds": 10,
                "debug": True,
            },
            "test_04_git_modified_medium_timeout": {
                "targets": None,
                "check_git_modified_files": True,
                "verbose": False,
                "timeout_seconds": 20,
                "debug": False,
            },
            "test_05_git_modified_long_timeout": {
                "targets": None,
                "check_git_modified_files": True,
                "verbose": True,
                "timeout_seconds": 50,
                "debug": True,
            },
            "test_06_relative_single_dir": {
                "targets": ["pdf2zh_next/"],
                "check_git_modified_files": False,
                "verbose": True,
                "timeout_seconds": 30,
                "debug": False,
            },
            "test_07_relative_multiple_dirs": {
                "targets": ["pdf2zh_next/config/", "pdf2zh_next/translator/"],
                "check_git_modified_files": False,
                "verbose": False,
                "timeout_seconds": 45,
                "debug": True,
            },
            "test_08_docs_directory": {
                "targets": ["docs/"],
                "check_git_modified_files": False,
                "verbose": False,
                "timeout_seconds": 75,
                "debug": False,
            },
            "test_09_single_file": {
                "targets": ["pyproject.toml"],
                "check_git_modified_files": False,
                "verbose": True,
                "timeout_seconds": 60,
                "debug": False,
            },
            "test_10_multiple_files": {
                "targets": [
                    "pdf2zh_next/config/model.py",
                    "pdf2zh_next/translator/utils.py",
                ],
                "check_git_modified_files": False,
                "verbose": True,
                "timeout_seconds": 35,
                "debug": False,
            },
            "test_11_nonexistent_file": {
                "targets": ["nonexistent_file.py"],
                "check_git_modified_files": False,
                "verbose": False,
                "timeout_seconds": 15,
                "debug": False,
            },
            "test_12_wildcard_pattern": {
                "targets": ["*.py"],
                "check_git_modified_files": False,
                "verbose": False,
                "timeout_seconds": 25,
                "debug": False,
            },
            "test_13_current_dir_explicit": {
                "targets": ["./"],
                "check_git_modified_files": False,
                "verbose": True,
                "timeout_seconds": 40,
                "debug": False,
            },
            "test_14_empty_string": {
                "targets": [""],
                "check_git_modified_files": False,
                "verbose": False,
                "timeout_seconds": 80,
                "debug": False,
            },
            "test_15_absolute_path_directory": {
                "targets": ["G:\\GitHub\\PDFMathTranslate"],
                "check_git_modified_files": False,
                "verbose": False,
                "timeout_seconds": 45,
                "debug": False,
                "root": "G:\\GitHub\\PDFMathTranslate",
            },
            "test_16_absolute_path_file": {
                "targets": [
                    "G:\\GitHub\\PDFMathTranslate\\pdf2zh_next\\config\\model.py"
                ],
                "check_git_modified_files": False,
                "verbose": True,
                "timeout_seconds": 30,
                "debug": False,
                "root": "G:\\GitHub\\PDFMathTranslate",
            },
            "test_17_null_targets_verbose": {
                "targets": None,
                "check_git_modified_files": False,
                "verbose": True,
                "timeout_seconds": 20,
                "debug": False,
            },
            "test_18_mixed_valid_invalid_paths": {
                "targets": ["pdf2zh_next/config/model.py", "nonexistent.py", "docs/"],
                "check_git_modified_files": False,
                "verbose": True,
                "timeout_seconds": 30,
                "debug": False,
            },
            "test_19_very_short_timeout": {
                "targets": ["docs/"],
                "check_git_modified_files": False,
                "verbose": False,
                "timeout_seconds": 1,
                "debug": False,
            },
            "test_20_max_timeout": {
                "targets": ["pdf2zh_next/"],
                "check_git_modified_files": False,
                "verbose": False,
                "timeout_seconds": 90,
                "debug": False,
            },
        }

        for name, params in test_data.items():
            self._run_test_case(name, params)


if __name__ == "__main__":
    unittest.main()
