# config.py
import os
import json

CONFIG_PATH = os.path.expanduser("~/.annotator_config.json")

DEFAULTS = {
    "annotator_id": "",
    "base_url": "http://127.0.0.1:8000"
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return DEFAULTS
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
