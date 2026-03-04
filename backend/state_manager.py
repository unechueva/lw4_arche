import json
import os
from pathlib import Path

STATE_PATH = "app/data/state.json"

class StateManager:
    @staticmethod
    def load():
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        if not os.path.exists(STATE_PATH):
            return {}
        with open(STATE_PATH, "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}

    @staticmethod
    def save(state):
        with open(STATE_PATH, "w") as f:
            json.dump(state, f, indent=4)

    @staticmethod
    def add_instance(instance: dict):
        state = StateManager.load()
        state[instance["id"]] = instance
        StateManager.save(state)

    @staticmethod
    def update_status(instance_id: str, status: str):
        state = StateManager.load()
        if instance_id in state:
            state[instance_id]["status"] = status
            StateManager.save(state)
