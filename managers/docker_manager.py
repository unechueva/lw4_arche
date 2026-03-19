import subprocess
import time
import threading
import os
from backend.state_manager import load_state, save_state

class DockerManager:
    SSH_PASSWORD = "toor"
    LIFETIME_SECONDS = 3600

    def __init__(self):
        self._ensure_image()

    def _ensure_image(self):
        """Один раз собираем образ, если его нет"""
        if not subprocess.run(["docker", "image", "inspect", "custom_ubuntu"], capture_output=True).returncode == 0:
            print("Собираем custom_ubuntu образ...")
            subprocess.run([
                "docker", "build", "-t", "custom_ubuntu",
                "-f", "images/Dockerfile.ubuntu", "."
            ], check=True)

    def create_container(self, cpu: int, ram: int, port: int, container_id: str):
        if cpu not in (1, 2):
            raise ValueError("CPU только 1 или 2")
        if ram not in (512, 1024):
            raise ValueError("RAM только 512 или 1024")

        cmd = [
            "docker", "run", "-d",
            f"--name={container_id}",
            f"-p", f"{port}:22",
            f"--cpus={cpu}",
            f"--memory={ram}m",
            "custom_ubuntu"
        ]

        subprocess.run(cmd, check=True)
        time.sleep(5)

        threading.Thread(target=self._auto_delete, args=(container_id,), daemon=True).start()

        return {
            "id": container_id,
            "type": "docker",
            "cpu": cpu,
            "ram": ram,
            "port": port,
            "status": "running"
        }

    def _auto_delete(self, container_id: str):
        time.sleep(self.LIFETIME_SECONDS)
        try:
            self.delete_container(container_id)
        except:
            pass

    def delete_container(self, container_id: str):
        subprocess.run(["docker", "rm", "-f", container_id], check=True)

    def list_containers(self):
        state = load_state()
        return [v for v in state.values() if v.get("type") == "docker"]
