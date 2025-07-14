import json
import os

def load_config(root_path):
    enforcer_dir = os.path.join(root_path, '.enforcer')
    if not os.path.exists(enforcer_dir):
        os.makedirs(enforcer_dir)
    config_path = os.path.join(enforcer_dir, 'config.json')  # Changed to inside .enforcer
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            json.dump({'disabled_rules': {}}, f)
    with open(config_path, 'r') as f:
        config = json.load(f)
    # Optionally load tool-specific configs from .enforcer/
    config['tool_configs'] = {}
    for file in os.listdir(enforcer_dir):
        if file.endswith('.json') and file != 'config.json':
            tool = file[:-5]
            with open(os.path.join(enforcer_dir, file), 'r') as f:
                config['tool_configs'][tool] = json.load(f)
    return config 