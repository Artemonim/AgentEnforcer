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
