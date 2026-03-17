import subprocess
import time
import threading
from backend.state_manager import StateManager

class DockerManager:
    SSH_PASSWORD = "toor"
    LIFETIME_SECONDS = 3600

    def create_container(self, cpu: int, ram: int, port: int, id: str, os: str = "ubuntu"):
        if cpu not in (1, 2):
            raise ValueError("CPU только 1 или 2")
        if ram not in (512, 1024):
            raise ValueError("RAM только 512 или 1024")

        image = "custom_ubuntu" if os == "ubuntu" else "custom_debian"

        setup_cmd = (
            "apt-get update -qq && apt-get install -y openssh-server && "
            f"echo 'root:{self.SSH_PASSWORD}' | chpasswd && "
            "sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config && "
            "sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && "
            "mkdir -p /run/sshd && exec /usr/sbin/sshd -D"
        )

        cmd = [
            "docker", "run", "-d",
            f"--name={id}",
            f"-p", f"{port}:22",
            f"--cpus={cpu}",
            f"--memory={ram}m",
            image,
            "bash", "-c", setup_cmd
        ]

        subprocess.run(cmd, check=True)
        time.sleep(6)
        threading.Thread(target=self._auto_delete, args=(id,), daemon=True).start()

        return {
            "id": id,
            "type": "docker",
            "cpu": cpu,
            "ram": ram,
            "port": port,
            "status": "running"
        }

    def _auto_delete(self, instance_id: str):
        time.sleep(self.LIFETIME_SECONDS)
        try:
            self.delete_container(instance_id)
            print(f"[AUTO] Контейнер {instance_id} удалён по таймеру")
        except:
            pass

    def delete_container(self, id: str):
        subprocess.run(["docker", "rm", "-f", id], check=True)

    def list_containers(self):
        state = StateManager.load()
        return [inst for inst in state.values()
                if inst.get("type") == "docker" and inst.get("status") != "deleted"]
