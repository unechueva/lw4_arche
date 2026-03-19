import subprocess
import time
import os
import signal
import shutil
from datetime import datetime
from backend.state_manager import load_state, save_state, add_object, delete_object
from backend.port_manager import get_next_port

class QemuManager:
    def __init__(self):
        self.base_image = "images/base-ubuntu-server.qcow2"
        self.images_dir = "images"

    def create_vm(self, cpu: int, ram: int, port: int, vm_id: str) -> dict:
        """Создаёт новую виртуальную машину"""
        if cpu not in (1, 2):
            raise ValueError("CPU только 1 или 2")
        if ram not in (512, 1024):
            raise ValueError("RAM только 512 или 1024")

        new_image = f"{self.images_dir}/{vm_id}.qcow2"
        shutil.copy(self.base_image, new_image)

        cmd = [
            "qemu-system-x86_64",
            "-m", str(ram),
            "-smp", str(cpu),
            "-drive", f"file={new_image},format=qcow2",
            "-boot", "c",
            "-net", "nic,model=virtio",
            "-net", f"user,hostfwd=tcp::{port}-:22",
            "-nographic",
            "-daemonize"
        ]

        subprocess.run(cmd, check=True)
        time.sleep(4)

        pid = self._get_qemu_pid(vm_id)

        data = {
            "id": vm_id,
            "type": "vm",
            "cpu": cpu,
            "ram": ram,
            "port": port,
            "status": "running",
            "pid": pid,
            "image_path": new_image
        }

        add_object(vm_id, data)
        return {
            "id": vm_id,
            "type": "vm",
            "cpu": cpu,
            "ram": ram,
            "port": port,
            "status": "running"
        }

    def _get_qemu_pid(self, vm_id: str) -> int:
        """Находит PID процесса QEMU по имени файла образа"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", f"{vm_id}.qcow2"],
                capture_output=True, text=True, check=True
            )
            pids = result.stdout.strip().split()
            if pids:
                return int(pids[0])
        except:
            pass
        return 0

    def delete_vm(self, vm_id: str):
        """Удаляет виртуальную машину"""
        state = load_state()
        if vm_id not in state:
            return

        info = state[vm_id]
        pid = info.get("pid")
        image_path = info.get("image_path")

        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                if os.path.exists(f"/proc/{pid}"):
                    os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except Exception as e:
                print(f"Ошибка при kill PID {pid}: {e}")

        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                print(f"Ошибка удаления образа {image_path}: {e}")

        delete_object(vm_id)

    def list_vms(self):
        """Возвращает список всех VM с актуальным статусом"""
        state = load_state()
        vms = []
        for vm_id, info in state.items():
            if info.get("type") != "vm":
                continue

            pid = info.get("pid")
            running = False
            if pid:
                try:
                    os.kill(pid, 0)
                    running = True
                except ProcessLookupError:
                    running = False
                except Exception:
                    running = False

            info_copy = info.copy()
            info_copy["status"] = "running" if running else "stopped"
            vms.append(info_copy)

        return vms
