import subprocess
import time
import threading
from datetime import datetime
from backend.state_manager import StateManager
from backend.port_manager import PortManager

class DockerManager:
    SSH_PASSWORD = "toor"
    LIFETIME_SECONDS = 300  

    def create_container(self, os: str, cpu: int, ram: int, port: int, id: str, user_id: str = None):
        if os not in ("ubuntu", "debian"):
            raise ValueError("os должен быть ubuntu или debian")
        if cpu not in (1, 2) or ram not in (512, 1024):
            raise ValueError("Неверные cpu/ram")

        image = f"custom_{os}"
        start_time = datetime.now().isoformat()

        cmd = [
            "docker", "run", "-d",
            f"--name={id}",
            f"-p", f"{port}:22",
            f"--cpus={cpu}",
            f"--memory={ram}m",
            image,
            "/usr/sbin/sshd", "-D"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        container_id = result.stdout.strip()

        instance = {
            "id": id,
            "type": "docker",
            "os": os,
            "cpu": cpu,
            "ram": ram,
            "port": port,
            "status": "running",
            "container_id": container_id,
            "start_time": start_time,
            "user_id": user_id
        }

        StateManager.add_instance(instance)
        threading.Thread(target=self._auto_delete, args=(id,), daemon=True).start()

        return instance

    def _auto_delete(self, instance_id: str):
        time.sleep(self.LIFETIME_SECONDS)
        try:
            self.delete_container(instance_id)
            print(f"[AUTO] Контейнер {instance_id} удалён по таймеру")
        except:
            pass

    def list_containers(self):
        state = StateManager.load()
        return [inst for inst in state.values() if inst.get("type") == "docker"]

    def delete_container(self, id: str):
        subprocess.run(["docker", "stop", id], check=True)
        subprocess.run(["docker", "rm", "-f", id], check=True)
        StateManager.update_status(id, "deleted")
