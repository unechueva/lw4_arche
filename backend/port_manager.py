# backend/port_manager.py
import json
import os
from typing import Optional

class PortManager:
    def __init__(self, state_file: str = "state.json"):
        self.state_file = state_file
        self.start_port = 2300
        
    def _load_state(self) -> dict:
        """Загружает состояние из файла"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {"vms": {}}
    
    def _save_state(self, state: dict):
        """Сохраняет состояние в файл"""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_next_port(self, vm_id: str) -> int:
        """
        Находит следующий свободный порт
        Начинаем с 2300, ищем максимальный использованный + 1
        """
        state = self._load_state()
        
        # Собираем все используемые порты
        used_ports = []
        for vm_data in state["vms"].values():
            if "port" in vm_data:
                used_ports.append(vm_data["port"])
        
        if not used_ports:
            return self.start_port
        
        # Берем максимальный порт + 1
        next_port = max(used_ports) + 1
        return next_port
    
    def reserve_port(self, vm_id: str, port: int):
        """Резервирует порт за ВМ"""
        state = self._load_state()
        if vm_id not in state["vms"]:
            state["vms"][vm_id] = {}
        state["vms"][vm_id]["port"] = port
        self._save_state(state)
    
    def release_port(self, vm_id: str):
        """Освобождает порт при удалении ВМ"""
        state = self._load_state()
        if vm_id in state["vms"]:
            if "port" in state["vms"][vm_id]:
                del state["vms"][vm_id]["port"]
            self._save_state(state)
