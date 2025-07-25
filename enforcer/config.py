import json
import os


def load_config(root_path):
    enforcer_dir = os.path.join(root_path, ".enforcer")
    if not os.path.exists(enforcer_dir):
        os.makedirs(enforcer_dir)
    config_path = os.path.join(
        enforcer_dir, "config.json"
    )  # Changed to inside .enforcer
    if not os.path.exists(config_path):
        # * Create a default config if it doesn't exist
        default_config = {"disabled_rules": {}, "debug_mode_enabled": False}
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        config = default_config
    else:
        with open(config_path, "r") as f:
            config = json.load(f)

    # * Ensure debug mode key exists for existing configs
    if "debug_mode_enabled" not in config:
        config["debug_mode_enabled"] = False

    # Optionally load tool-specific configs from .enforcer/
    config["tool_configs"] = {}
    for file in os.listdir(enforcer_dir):
        if file.endswith(".json") and file != "config.json":
            tool = file[:-5]
            with open(os.path.join(enforcer_dir, file), "r") as f:
                config["tool_configs"][tool] = json.load(f)
    return config


def save_config(root_path, config):
    enforcer_dir = os.path.join(root_path, ".enforcer")
    config_path = os.path.join(enforcer_dir, "config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
