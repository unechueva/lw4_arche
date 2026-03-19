import json
import os

STATE_FILE = "data/state.json"

def get_next_port(resource_type: str) -> int:
    """Возвращает следующий свободный порт: 2222 для docker, 2300 для vm"""
    start_port = 2222 if resource_type == "docker" else 2300
    if not os.path.exists(STATE_FILE):
        return start_port
    
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    
    used_ports = [obj.get("port", 0) for obj in state.values()]
    if not used_ports:
        return start_port
    return max(used_ports) + 1
