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
    file = tmp_path / "test.py"
    file.write_text("code")
    with patch.object(enforcer, "get_language", return_value="python"):
        files_by_lang, messages = enforcer.scan_files()
        assert files_by_lang == {"python": [str(file)]}
        assert not messages


def test_get_language():
    enforcer = Enforcer(".")
    # This should return None for unknown extensions
    result = enforcer.get_language("test.unknown")
    assert result is None


@patch("enforcer.core.subprocess.run")
def test_run_checks_empty_files(mock_run, enforcer):
    enforcer.scan_files = MagicMock(return_value=({}, []))
    enforcer.presenter = MagicMock()
    result = enforcer.run_checks()
    enforcer.presenter.status.assert_called_with("No files to check.", "warning")


def test_get_language_python(enforcer):
    result = enforcer.get_language("test.py")
    assert result == "python"


def test_run_checks_structured(tmp_path):
    enforcer = Enforcer(str(tmp_path))
    enforcer.scan_files = MagicMock(return_value=({}, []))
    result = enforcer.run_checks_structured()
    assert result == {
        "errors": [],
        "warnings": [],
        "messages": ["No files to check."],
    }


def test_run_checks_structured_no_warnings(tmp_path):
    enforcer = Enforcer(str(tmp_path))
    enforcer.scan_files = MagicMock(return_value=({}, []))
    with patch.object(enforcer, "setup_logging", return_value=(MagicMock(), MagicMock())):
        result = enforcer.run_checks_structured()
        assert result == {
            "errors": [],
            "warnings": [],
            "messages": ["No files to check."],
        }


def test_run_checks_structured_with_issues(tmp_path):
    enforcer = Enforcer(str(tmp_path))

    # Mock plugins and scan_files to return some mock data
    mock_plugin = MagicMock()
    mock_plugin.autofix_style.return_value = {"changed_count": 2}
    mock_plugin.lint.return_value = {
        "errors": [{"file": "test.py", "line": 1, "message": "Test error"}],
        "warnings": [{"file": "test.py", "line": 2, "message": "Test warning"}],
    }

    enforcer.plugins = {"python": mock_plugin}
    enforcer.scan_files = MagicMock(return_value=({"python": ["test.py"]}, []))
    enforcer.check_tools = MagicMock(return_value=True)

    with patch.object(enforcer, "setup_logging", return_value=(MagicMock(), MagicMock())):
        result = enforcer.run_checks_structured()

        assert len(result["errors"]) == 1
        assert len(result["warnings"]) == 1
        assert result["formatted_files"] == 2


# * Fixture Detection Tests


@pytest.fixture
def enforcer_with_fixtures_disabled(tmp_path):
    """Enforcer with check_fixtures = False (default behavior)."""
    config = {
        "check_fixtures": False,
        "custom_fixture_patterns": {"directories": [], "files": []},
    }
    return Enforcer(str(tmp_path), config=config)


@pytest.fixture
def enforcer_with_fixtures_enabled(tmp_path):
    """Enforcer with check_fixtures = True (include fixtures in checking)."""
    config = {
        "check_fixtures": True,
        "custom_fixture_patterns": {"directories": [], "files": []},
    }
    return Enforcer(str(tmp_path), config=config)


def test_is_fixture_directory_standard_patterns(enforcer_with_fixtures_disabled):
    """Test detection of standard fixture directory patterns."""
    # Python patterns
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("testdata", "tests")
        is True
    )
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("fixtures", "tests")
        is True
    )
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("test_fixtures", "tests")
        is True
    )

    # JavaScript/TypeScript patterns
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("__fixtures__", "tests")
        is True
    )
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("mocks", "tests") is True
    )

    # C# patterns
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("TestData", "tests")
        is True
    )
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("Fixtures", "tests")
        is True
    )
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("Resources", "tests")
        is True
    )


def test_is_fixture_directory_case_insensitive(enforcer_with_fixtures_disabled):
    """Test that fixture detection is case insensitive."""
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("FIXTURES", "tests")
        is True
    )
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("testdata", "tests")
        is True
    )
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("TestData", "tests")
        is True
    )


def test_is_fixture_directory_in_test_context(enforcer_with_fixtures_disabled):
    """Test fixture detection when inside test directories."""
    # Should detect fixture patterns when inside test directories
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("data", "tests/unit")
        is True
    )
    assert enforcer_with_fixtures_disabled._is_fixture_directory("mock", "spec") is True
    assert (
        enforcer_with_fixtures_disabled._is_fixture_directory("stub", "__tests__")
        is True
    )

    # Should not detect when not in test directory
    assert enforcer_with_fixtures_disabled._is_fixture_directory("data", "src") is False


def test_is_fixture_directory_with_check_fixtures_enabled(
    enforcer_with_fixtures_enabled,
):
    """Test that fixture directories are not excluded when check_fixtures=True."""
    # When check_fixtures is True, should NOT exclude fixture directories
    assert (
        enforcer_with_fixtures_enabled._is_fixture_directory("fixtures", "tests")
        is False
    )
    assert (
        enforcer_with_fixtures_enabled._is_fixture_directory("testdata", "tests")
        is False
    )
    assert (
        enforcer_with_fixtures_enabled._is_fixture_directory("__fixtures__", "tests")
        is False
    )


def test_is_fixture_file_standard_patterns(enforcer_with_fixtures_disabled):
    """Test detection of standard fixture file patterns."""
    # Files in fixture directories should be excluded
    assert (
        enforcer_with_fixtures_disabled._is_fixture_file("tests/fixtures/test.py")
        is True
    )
    assert (
        enforcer_with_fixtures_disabled._is_fixture_file("tests/testdata/sample.json")
        is True
    )

    # Files with fixture patterns in name (but not test files)
    assert enforcer_with_fixtures_disabled._is_fixture_file("sample_data.py") is True
    assert (
        enforcer_with_fixtures_disabled._is_fixture_file("mock_response.json") is True
    )
    assert enforcer_with_fixtures_disabled._is_fixture_file("fixture_helper.py") is True


def test_is_fixture_file_preserves_test_files(enforcer_with_fixtures_disabled):
    """Test that actual test files are never excluded, even with fixture patterns."""
    # These should NOT be excluded because they are clearly test files
    assert enforcer_with_fixtures_disabled._is_fixture_file("test_fixture.py") is False
    assert enforcer_with_fixtures_disabled._is_fixture_file("fixture_test.py") is False
    assert enforcer_with_fixtures_disabled._is_fixture_file("sample.test.js") is False
    assert enforcer_with_fixtures_disabled._is_fixture_file("mock.spec.ts") is False


def test_is_fixture_file_with_check_fixtures_enabled(enforcer_with_fixtures_enabled):
    """Test that fixture files are not excluded when check_fixtures=True."""
    # When check_fixtures is True, should NOT exclude fixture files
    assert (
        enforcer_with_fixtures_enabled._is_fixture_file("tests/fixtures/test.py")
        is False
    )
    assert enforcer_with_fixtures_enabled._is_fixture_file("sample_data.py") is False
    assert (
        enforcer_with_fixtures_enabled._is_fixture_file("mock_response.json") is False
    )


def test_custom_fixture_patterns(tmp_path):
    """Test custom fixture patterns configuration."""
    config = {
        "check_fixtures": False,
        "custom_fixture_patterns": {
            "directories": ["my_fixtures", "test_data"],
            "files": ["sample", "mock_data"],
        },
    }
    enforcer = Enforcer(str(tmp_path), config=config)

    # Custom directory patterns should be detected
    assert enforcer._is_fixture_directory("my_fixtures", "tests") is True
    assert enforcer._is_fixture_directory("test_data", "tests") is True

    # Custom file patterns should be detected
    assert enforcer._is_fixture_file("sample.py") is True
    assert enforcer._is_fixture_file("mock_data.json") is True


def test_scan_files_excludes_fixtures(tmp_path):
    """Test that scan_files properly excludes fixture files and directories."""
    # Create test structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_main(): pass")

    (tmp_path / "tests" / "fixtures").mkdir()
    (tmp_path / "tests" / "fixtures" / "broken.py").write_text(
        "def broken( # intentionally broken"
    )

    config = {
        "check_fixtures": False,
        "custom_fixture_patterns": {"directories": [], "files": []},
    }
    enforcer = Enforcer(str(tmp_path), config=config)

    with patch.object(enforcer, "get_language", return_value="python"):
        files_by_lang, messages = enforcer.scan_files()

        python_files = files_by_lang.get("python", [])

        # Should include main source and test files
        assert any("main.py" in f for f in python_files)
        assert any("test_main.py" in f for f in python_files)

        # Should NOT include fixture files
        assert not any("broken.py" in f for f in python_files)


def test_scan_files_includes_fixtures_when_enabled(tmp_path):
    """Test that scan_files includes fixture files when check_fixtures=True."""
    # Create test structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "fixtures").mkdir()
    (tmp_path / "tests" / "fixtures" / "broken.py").write_text(
        "def broken( # intentionally broken"
    )

    config = {
        "check_fixtures": True,
        "custom_fixture_patterns": {"directories": [], "files": []},
    }
    enforcer = Enforcer(str(tmp_path), config=config)

    with patch.object(enforcer, "get_language", return_value="python"):
        files_by_lang, messages = enforcer.scan_files()

        python_files = files_by_lang.get("python", [])

        # Should include both main and fixture files
        assert any("main.py" in f for f in python_files)
        assert any("broken.py" in f for f in python_files)
