import json
import os

STATE_FILE = "data/state.json"

def get_next_port(resource_type: str) -> int:
    start_port = 2222 if resource_type == "docker" else 2300
    
    if not os.path.exists(STATE_FILE):
        return start_port
    
    with open(STATE_FILE, 'r') as f:
        content = f.read().strip()
        if not content:
            return start_port
        state = json.loads(content)
    
    used_ports = [obj.get("port", 0) for obj in state.values() if isinstance(obj.get("port"), int)]
    if not used_ports:
        return start_port
    return max(used_ports) + 1
