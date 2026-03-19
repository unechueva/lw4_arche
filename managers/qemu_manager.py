# managers/qemu_manager.py (Windows версия)
import subprocess
import os
import signal
import shutil
import json
import time
import threading
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class QEMUManager:
    def __init__(self, images_dir: str = "images", state_file: str = "state.json"):
        self.images_dir = images_dir
        self.state_file = state_file
        self.base_images = {
            "ubuntu": "base-ubuntu-server.qcow2",
            "debian": "base-debian.qcow2"
        }
        self.monitor_threads = {}
        
        # Определяем путь к QEMU в зависимости от ОС
        self.qemu_path = self._find_qemu()
        
        # Создаем папку для images
        Path(images_dir).mkdir(exist_ok=True)
    
    def _find_qemu(self) -> str:
        """Находит путь к qemu-system-x86_64.exe"""
        # Возможные пути установки QEMU в Windows
        possible_paths = [
            "qemu-system-x86_64",  # если в PATH
            r"C:\Program Files\qemu\qemu-system-x86_64.exe",
            r"C:\Program Files (x86)\qemu\qemu-system-x86_64.exe",
        ]
        
        for path in possible_paths:
            try:
                subprocess.run([path, "--version"], capture_output=True, check=True)
                return path
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        raise Exception("QEMU not found. Please install QEMU and add to PATH")
    
    def _load_state(self) -> dict:
        """Загружает состояние из файла"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"vms": {}}
    
    def _save_state(self, state: dict):
        """Сохраняет состояние в файл"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def create_vm(self, os_type: str, cpu: int, ram: int, port: int, 
                  vm_id: str, user_id: str, timeout_minutes: int = 5) -> Dict:
        """
        Создает новую виртуальную машину (Windows версия)
        """
        # 1. Проверяем базовый образ
        base_image = self.base_images.get(os_type)
        if not base_image:
            raise ValueError(f"Unsupported OS type: {os_type}")
        
        base_image_path = os.path.join(self.images_dir, base_image)
        if not os.path.exists(base_image_path):
            raise FileNotFoundError(f"Base image not found: {base_image_path}")
        
        # 2. Создаем копию
        new_image_path = os.path.join(self.images_dir, f"{vm_id}.qcow2")
        shutil.copy(base_image_path, new_image_path)
        print(f"Created copy: {new_image_path}")
        
        # 3. Формируем команду (одной строкой для Windows)
        cmd = [
            self.qemu_path,
            "-m", str(ram),
            "-smp", str(cpu),
            "-drive", f"file={new_image_path},format=qcow2",
            "-boot", "c",
            "-net", "nic,model=virtio",
            "-net", f"user,hostfwd=tcp::{port}-:22",
            "-nographic"
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        # 4. Запускаем процесс
        try:
            # В Windows используем CREATE_NO_WINDOW для скрытия окна
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        except Exception as e:
            print(f"Error starting QEMU: {e}")
            # Удаляем созданный образ если не удалось запустить
            if os.path.exists(new_image_path):
                os.remove(new_image_path)
            raise
        
        # Даем время на запуск
        time.sleep(3)
        
        # 5. Проверяем что процесс запустился
        if process.poll() is not None:
            # Процесс завершился с ошибкой
            stderr = process.stderr.read().decode('cp1251', errors='ignore')
            stdout = process.stdout.read().decode('cp1251', errors='ignore')
            print(f"QEMU stderr: {stderr}")
            print(f"QEMU stdout: {stdout}")
            
            if os.path.exists(new_image_path):
                os.remove(new_image_path)
            raise Exception(f"QEMU failed to start: {stderr}")
        
        # 6. Сохраняем информацию
        start_time = time.time()
        vm_info = {
            "id": vm_id,
            "user_id": user_id,
            "os_type": os_type,
            "cpu": cpu,
            "ram": ram,
            "port": port,
            "pid": process.pid,
            "start_time": start_time,
            "timeout_minutes": timeout_minutes,
            "image_path": new_image_path,
            "created_at": datetime.now().isoformat()
        }
        
        state = self._load_state()
        state["vms"][vm_id] = vm_info
        self._save_state(state)
        
        # Запускаем мониторинг
        self._start_monitoring(vm_id, timeout_minutes * 60)
        
        return vm_info
    
    def list_vms(self) -> List[Dict]:
        """Возвращает список всех ВМ (Windows версия)"""
        state = self._load_state()
        vms = []
        
        # Получаем список процессов Windows
        try:
            # Используем tasklist для Windows
            tasklist = subprocess.check_output(['tasklist'], text=True)
            qemu_processes = [line for line in tasklist.split('\n') if 'qemu-system' in line.lower()]
        except subprocess.CalledProcessError:
            qemu_processes = []
        
        for vm_id, vm_info in state["vms"].items():
            # Проверяем жив ли процесс
            is_running = False
            if 'pid' in vm_info:
                try:
                    # В Windows используем специальный способ проверки процесса
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    SYNCHRONIZE = 0x00100000
                    handle = kernel32.OpenProcess(SYNCHRONIZE, False, vm_info['pid'])
                    if handle:
                        kernel32.CloseHandle(handle)
                        is_running = True
                except:
                    try:
                        # Альтернативный способ - через taskkill с проверкой
                        subprocess.run(['taskkill', '/PID', str(vm_info['pid']), '/F'], 
                                     capture_output=True, check=False)
                        is_running = True
                    except:
                        is_running = False
            
            vm_copy = vm_info.copy()
            vm_copy['status'] = 'running' if is_running else 'stopped'
            
            if is_running and 'start_time' in vm_copy:
                uptime = time.time() - vm_copy['start_time']
                vm_copy['uptime_seconds'] = int(uptime)
            
            vms.append(vm_copy)
        
        return vms
    
    def delete_vm(self, vm_id: str):
        """Удаляет виртуальную машину (Windows версия)"""
        state = self._load_state()
        
        if vm_id not in state["vms"]:
            raise ValueError(f"VM {vm_id} not found")
        
        vm_info = state["vms"][vm_id]
        
        # 1. Останавливаем процесс
        if 'pid' in vm_info:
            try:
                # В Windows используем taskkill
                subprocess.run(['taskkill', '/PID', str(vm_info['pid']), '/F'], 
                             capture_output=True, check=True)
                print(f"Killed process {vm_info['pid']}")
            except subprocess.CalledProcessError:
                print(f"Process {vm_info['pid']} already terminated or not found")
            except Exception as e:
                print(f"Error killing process: {e}")
        
        # 2. Удаляем образ
        if 'image_path' in vm_info and os.path.exists(vm_info['image_path']):
            try:
                os.remove(vm_info['image_path'])
                print(f"Deleted image: {vm_info['image_path']}")
            except Exception as e:
                print(f"Error deleting image: {e}")
        
        # 3. Удаляем из state
        del state["vms"][vm_id]
        self._save_state(state)
        
        # 4. Останавливаем мониторинг
        if vm_id in self.monitor_threads:
            del self.monitor_threads[vm_id]
    
    def _monitor_vm(self, vm_id: str, timeout_seconds: int):
        """Мониторит время жизни ВМ"""
        start_time = time.time()
        
        while True:
            time.sleep(60)
            
            state = self._load_state()
            if vm_id not in state["vms"]:
                break
            
            vm_info = state["vms"][vm_id]
            
            elapsed = time.time() - vm_info.get('start_time', start_time)
            if elapsed > timeout_seconds:
                print(f"VM {vm_id} timeout reached ({timeout_seconds}s). Deleting...")
                self.delete_vm(vm_id)
                break
            
            if 'pid' in vm_info:
                try:
                    # Проверяем процесс
                    subprocess.run(['taskkill', '/PID', str(vm_info['pid']), '/F'], 
                                 capture_output=True, check=False)
                except:
                    print(f"VM {vm_id} process died unexpectedly")
                    self.delete_vm(vm_id)
                    break
    
    def _start_monitoring(self, vm_id: str, timeout_seconds: int):
        """Запускает мониторинг"""
        monitor_thread = threading.Thread(
            target=self._monitor_vm,
            args=(vm_id, timeout_seconds),
            daemon=True
        )
        monitor_thread.start()
        self.monitor_threads[vm_id] = monitor_thread
        print(f"Started monitoring for VM {vm_id}")
    
    def get_vm_info(self, vm_id: str) -> Optional[Dict]:
        """Получает информацию о ВМ"""
        state = self._load_state()
        return state["vms"].get(vm_id)
    
    def get_ssh_command(self, vm_id: str) -> str:
        """Возвращает SSH команду"""
        vm_info = self.get_vm_info(vm_id)
        if not vm_info:
            return f"VM {vm_id} not found"
        
        # Для Windows SSH может быть через PuTTY или встроенный OpenSSH
        return f"ssh unechueva@localhost -p {vm_info['port']}"
