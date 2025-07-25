import os

import pytest

from enforcer.config import load_config, save_config


def test_load_config(tmp_path):
    os.makedirs(tmp_path / ".enforcer")
    config_file = tmp_path / ".enforcer" / "config.json"
    config_file.write_text('{"disabled_rules": {"python": ["E501"]}}')
    config = load_config(str(tmp_path))
    assert config["disabled_rules"]["python"] == ["E501"]


def test_save_config(tmp_path):
    os.makedirs(tmp_path / ".enforcer")
    config = {"test": "value"}
    save_config(str(tmp_path), config)
    config_file = tmp_path / ".enforcer" / "config.json"
    assert config_file.exists()
    loaded = load_config(str(tmp_path))
    assert loaded["test"] == "value"


def test_default_config_creation(tmp_path):
    """Test that default config is created with all required keys."""
    config = load_config(str(tmp_path))

    # * Check all default keys exist
    assert "disabled_rules" in config
    assert "debug_mode_enabled" in config
    assert "check_fixtures" in config
    assert "custom_fixture_patterns" in config

    # * Check default values
    assert config["disabled_rules"] == {}
    assert config["debug_mode_enabled"] is False
    assert config["check_fixtures"] is False
    assert config["custom_fixture_patterns"] == {"directories": [], "files": []}


def test_debug_mode_enabled_flag(tmp_path):
    """Test debug_mode_enabled flag functionality."""
    # Create config with debug enabled
    os.makedirs(tmp_path / ".enforcer")
    config_file = tmp_path / ".enforcer" / "config.json"
    config_file.write_text('{"debug_mode_enabled": true}')

    config = load_config(str(tmp_path))
    assert config["debug_mode_enabled"] is True


def test_check_fixtures_flag(tmp_path):
    """Test check_fixtures flag functionality."""
    # Create config with fixtures checking enabled
    os.makedirs(tmp_path / ".enforcer")
    config_file = tmp_path / ".enforcer" / "config.json"
    config_file.write_text('{"check_fixtures": true}')

    config = load_config(str(tmp_path))
    assert config["check_fixtures"] is True


def test_custom_fixture_patterns(tmp_path):
    """Test custom_fixture_patterns configuration."""
    # Create config with custom patterns
    os.makedirs(tmp_path / ".enforcer")
    config_file = tmp_path / ".enforcer" / "config.json"
    config_file.write_text(
        """
    {
        "custom_fixture_patterns": {
            "directories": ["my_fixtures", "test_data"],
            "files": ["sample", "mock_data"]
        }
    }
    """
    )

    config = load_config(str(tmp_path))
    assert config["custom_fixture_patterns"]["directories"] == [
        "my_fixtures",
        "test_data",
    ]
    assert config["custom_fixture_patterns"]["files"] == ["sample", "mock_data"]


def test_config_migration_from_skip_fixture_exclusion(tmp_path):
    """Test migration from old skip_fixture_exclusion to new check_fixtures."""
    # Create config with old flag
    os.makedirs(tmp_path / ".enforcer")
    config_file = tmp_path / ".enforcer" / "config.json"
    config_file.write_text('{"skip_fixture_exclusion": true}')

    config = load_config(str(tmp_path))

    # * Old flag should be removed
    assert "skip_fixture_exclusion" not in config

    # * New flag should be set to same value (true -> true, both mean "include fixtures")
    assert config["check_fixtures"] is True

    # Test the opposite migration
    config_file.write_text('{"skip_fixture_exclusion": false}')
    config = load_config(str(tmp_path))
    assert (
        config["check_fixtures"] is False
    )  # false -> false (both mean "exclude fixtures")


def test_config_migration_preserves_other_settings(tmp_path):
    """Test that migration preserves other configuration settings."""
    os.makedirs(tmp_path / ".enforcer")
    config_file = tmp_path / ".enforcer" / "config.json"
    config_file.write_text(
        """
    {
        "disabled_rules": {"python": ["E501"]},
        "debug_mode_enabled": true,
        "skip_fixture_exclusion": true,
        "custom_fixture_patterns": {"directories": ["test"]}
    }
    """
    )

    config = load_config(str(tmp_path))

    # * Check migration worked
    assert "skip_fixture_exclusion" not in config
    assert (
        config["check_fixtures"] is True
    )  # skip_fixture_exclusion=True -> check_fixtures=True

    # * Check other settings preserved
    assert config["disabled_rules"]["python"] == ["E501"]
    assert config["debug_mode_enabled"] is True
    assert config["custom_fixture_patterns"]["directories"] == ["test"]


def test_backward_compatibility_with_missing_keys(tmp_path):
    """Test that missing keys are added with default values."""
    # Create config missing new keys
    os.makedirs(tmp_path / ".enforcer")
    config_file = tmp_path / ".enforcer" / "config.json"
    config_file.write_text('{"disabled_rules": {"python": ["E501"]}}')

    config = load_config(str(tmp_path))

    # * Should add missing keys with defaults
    assert config["debug_mode_enabled"] is False
    assert config["check_fixtures"] is False
    assert config["custom_fixture_patterns"] == {"directories": [], "files": []}

    # * Should preserve existing settings
    assert config["disabled_rules"]["python"] == ["E501"]
