import subprocess
import time

class DockerManager:
    SSH_PASSWORD = "toor"

    def create_container(self, cpu: int, ram: int, port: int, id: str):
        if cpu not in (1, 2):
            raise ValueError("CPU должен быть 1 или 2")
        if ram not in (512, 1024):
            raise ValueError("RAM должен быть 512 или 1024")


        setup_cmd = (
            "apt-get update -qq && "
            "apt-get install -y openssh-server && "
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
            "ubuntu:22.04",
            "bash", "-c", setup_cmd
        ]


        subprocess.run(cmd, check=True)

        time.sleep(6)
        return {
            "id": id,
            "type": "docker",
            "cpu": cpu,
            "ram": ram,
            "port": port,
            "status": "running"
        }

    def delete_container(self, id: str):
        subprocess.run(["docker", "rm", "-f", id], check=True)

    def list_containers(self):
        from backend.state_manager import StateManager
        state = StateManager.load()
        return [inst for inst in state.values() if inst.get("type") == "docker"]
