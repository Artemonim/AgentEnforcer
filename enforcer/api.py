from .core import Enforcer
from .config import load_config
import json

def run_enforcer(path=None, root_path='.', config=None):
    config = config or load_config(root_path)
    enforcer = Enforcer(root_path, path, config)
    errors = enforcer.run_checks()
    return {'errors': errors, 'summary': 'Brief summary here'}

def run_enforcer_json(*args, **kwargs):
    return json.dumps(run_enforcer(*args, **kwargs)) 