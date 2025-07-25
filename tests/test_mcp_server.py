import asyncio
import os
import platform
import unittest
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from enforcer.mcp_server import AgentEnforcerMCP, _uri_to_path, check_code

test_data = {
    "test_01_basic_no_targets": {
        "resource_uris": None,
        "check_git_modified_files": False,
        "verbose": False,
        "timeout_seconds": 15,
        "debug": False,
    },
    "test_02_basic_no_targets_debug": {
        "resource_uris": None,
        "check_git_modified_files": False,
        "verbose": False,
        "timeout_seconds": 90,
        "debug": True,
    },
    "test_03_git_modified_short_timeout": {
        "resource_uris": None,
        "check_git_modified_files": True,
        "verbose": False,
        "timeout_seconds": 10,
        "debug": True,
    },
    "test_04_git_modified_medium_timeout": {
        "resource_uris": None,
        "check_git_modified_files": True,
        "verbose": False,
        "timeout_seconds": 20,
        "debug": False,
    },
    "test_05_git_modified_long_timeout": {
        "resource_uris": None,
        "check_git_modified_files": True,
        "verbose": True,
        "timeout_seconds": 50,
        "debug": True,
    },
    "test_06_relative_single_dir": {
        "resource_uris": ["pdf2zh_next/"],
        "check_git_modified_files": False,
        "verbose": True,
        "timeout_seconds": 30,
        "debug": False,
    },
    "test_07_relative_multiple_dirs": {
        "resource_uris": ["pdf2zh_next/config/", "pdf2zh_next/translator/"],
        "check_git_modified_files": False,
        "verbose": False,
        "timeout_seconds": 45,
        "debug": True,
    },
    "test_08_docs_directory": {
        "resource_uris": ["docs/"],
        "check_git_modified_files": False,
        "verbose": False,
        "timeout_seconds": 75,
        "debug": False,
    },
    "test_09_single_file": {
        "resource_uris": ["pyproject.toml"],
        "check_git_modified_files": False,
        "verbose": True,
        "timeout_seconds": 60,
        "debug": False,
    },
    "test_10_multiple_files": {
        "resource_uris": [
            "pdf2zh_next/config/model.py",
            "pdf2zh_next/translator/utils.py",
        ],
        "check_git_modified_files": False,
        "verbose": True,
        "timeout_seconds": 35,
        "debug": False,
    },
    "test_11_nonexistent_file": {
        "resource_uris": ["nonexistent_file.py"],
        "check_git_modified_files": False,
        "verbose": False,
        "timeout_seconds": 15,
        "debug": False,
    },
    "test_12_wildcard_pattern": {
        "resource_uris": ["*.py"],
        "check_git_modified_files": False,
        "verbose": False,
        "timeout_seconds": 25,
        "debug": False,
    },
    "test_13_current_dir_explicit": {
        "resource_uris": ["./"],
        "check_git_modified_files": False,
        "verbose": True,
        "timeout_seconds": 40,
        "debug": False,
    },
    "test_14_empty_string": {
        "resource_uris": [""],
        "check_git_modified_files": False,
        "verbose": False,
        "timeout_seconds": 80,
        "debug": False,
    },
    "test_15_absolute_path_directory": {
        "resource_uris": ["file:///G:/GitHub/PDFMathTranslate"],
        "check_git_modified_files": False,
        "verbose": False,
        "timeout_seconds": 45,
        "debug": False,
        "root": "G:\\GitHub\\PDFMathTranslate",
    },
    "test_16_absolute_path_file": {
        "resource_uris": [
            "file:///G:/GitHub/PDFMathTranslate/pdf2zh_next/config/model.py"
        ],
        "check_git_modified_files": False,
        "verbose": True,
        "timeout_seconds": 30,
        "debug": False,
        "root": "G:\\GitHub\\PDFMathTranslate",
    },
    "test_17_null_targets_verbose": {
        "resource_uris": None,
        "check_git_modified_files": False,
        "verbose": True,
        "timeout_seconds": 20,
        "debug": False,
    },
    "test_18_mixed_valid_invalid_paths": {
        "resource_uris": ["pdf2zh_next/config/model.py", "nonexistent.py", "docs/"],
        "check_git_modified_files": False,
        "verbose": True,
        "timeout_seconds": 30,
        "debug": False,
    },
    "test_19_very_short_timeout": {
        "resource_uris": ["docs/"],
        "check_git_modified_files": False,
        "verbose": False,
        "timeout_seconds": 1,
        "debug": False,
    },
    "test_20_max_timeout": {
        "resource_uris": ["pdf2zh_next/"],
        "check_git_modified_files": False,
        "verbose": False,
        "timeout_seconds": 90,
        "debug": False,
    },
}


@pytest.fixture
def mcp_server():
    return AgentEnforcerMCP()


@pytest.mark.parametrize("params", test_data.values(), ids=test_data.keys())
def test_check_code_scenarios(params):
    """Helper to run a single test case."""
    resource_uris = params.get("resource_uris")
    with patch("enforcer.mcp_server.get_git_modified_files") as mock_git_files:
        mock_git_files.return_value = ["modified_file.py"]
        result = asyncio.run(
            check_code(
                resource_uris=resource_uris,
                check_git_modified_files=params["check_git_modified_files"],
                verbose=params["verbose"],
                timeout_seconds=params["timeout_seconds"],
                debug=params["debug"],
                root=params.get("root", os.getcwd()),
            )
        )
        if params["check_git_modified_files"]:
            mock_git_files.assert_called_once()
        assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_list_resources():
    mcp = AgentEnforcerMCP()
    with patch("enforcer.mcp_server.get_context") as mock_get_context, patch(
        "enforcer.mcp_server._uri_to_path", return_value="/root"
    ), patch("enforcer.mcp_server.Enforcer") as MockEnforcer, patch(
        "os.path.isdir", return_value=True
    ), patch(
        "enforcer.mcp_server.load_config", return_value={}
    ) as mock_load_config:

        mock_ctx = MagicMock()
        mock_root = MagicMock()
        mock_root.uri = "file:///root"
        mock_ctx.list_roots = AsyncMock(return_value=[mock_root])
        mock_get_context.return_value = mock_ctx

        mock_enforcer_instance = MockEnforcer.return_value
        mock_enforcer_instance.scan_files.return_value = (
            {"python": ["/root/file.py"]},
            [],
        )

        resources = await mcp._list_resources()

        assert len(resources) == 1
        MockEnforcer.assert_called_with(root_path="/root", config={})


def test_init():
    mcp = AgentEnforcerMCP()
    assert mcp.name == "agent_enforcer"


def test_uri_to_path_windows():
    with patch("platform.system", return_value="Windows"):
        assert _uri_to_path("file:///G:/foo/bar") == "G:\\foo\\bar"
        assert _uri_to_path("file:///C:/path/with%20space") == "C:\\path\\with space"
        assert _uri_to_path("/local/path") == "\\local\\path"


def test_uri_to_path_non_windows():
    with patch("platform.system", return_value="Linux"):
        assert _uri_to_path("file:///home/user/file") == "/home/user/file"
        assert _uri_to_path("file:///path/with%20space") == "/path/with space"


def test_uri_to_path_regression_mixed_separators():
    """
    Tests that paths with mixed separators and parent directory components
    are correctly normalized regardless of the host OS.
    """
    # Test case for Windows: mixed separators and .. should resolve correctly
    with patch("platform.system", return_value="Windows"):
        assert (
            _uri_to_path("file:///C:/Users/test/../project/file.txt")
            == "C:\\Users\\project\\file.txt"
        )
        assert (
            _uri_to_path("C:/Users/test/../project/file.txt")
            == "C:\\Users\\project\\file.txt"
        )

    # Test case for Linux: mixed separators and .. should resolve correctly
    with patch("platform.system", return_value="Linux"):
        assert (
            _uri_to_path("file:///home/user/../project/file.txt")
            == "/home/project/file.txt"
        )
        assert _uri_to_path("/home/user/../project/file.txt") == "/home/project/file.txt"


@pytest.mark.asyncio
async def test_check_code_no_root_fallback():
    with patch("enforcer.mcp_server.get_context") as mock_get_context, patch(
        "enforcer.mcp_server.get_git_root", return_value="/fake_root"
    ), patch("enforcer.mcp_server.os.path.isdir", return_value=True), patch(
        "enforcer.mcp_server.load_config", return_value={}
    ), patch(
        "enforcer.mcp_server.Enforcer"
    ) as mock_enforcer:
        mock_ctx = AsyncMock()
        mock_ctx.list_roots.return_value = []
        mock_get_context.return_value = mock_ctx
        result = await check_code()
        assert "root" not in result  # Assuming it proceeds with git root


@pytest.mark.asyncio
async def test_check_code_root_detection_error():
    with patch("enforcer.mcp_server.get_context") as mock_get_context, patch(
        "enforcer.mcp_server.get_git_root", return_value=None
    ):
        mock_ctx = AsyncMock()
        mock_ctx.list_roots.side_effect = Exception("client error")
        mock_get_context.return_value = mock_ctx
        result = await check_code()
        assert "error" in result
        assert "auto-detect" in result["error"]
