import json
import os

STATE_FILE = "data/state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, 'r') as f:
        content = f.read().strip()
        if not content:
            return {}
        return json.loads(content)

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

def add_object(obj_id, data):
    state = load_state()
    state[obj_id] = data
    save_state(state)

def delete_object(obj_id):
    state = load_state()
    if obj_id in state:
        del state[obj_id]
        save_state(state)
