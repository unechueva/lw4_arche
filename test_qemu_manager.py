# test_windows.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import sys
from backend.port_manager import PortManager
from managers.qemu_manager import QEMUManager

def main():
    print("=" * 50)
    print("Тестирование QEMU Manager (Windows)")
    print("=" * 50)
    
    # Проверяем существование папки images
    if not os.path.exists("images"):
        os.makedirs("images")
        print("Создана папка images")
    
    # Проверяем наличие базового образа
    base_image = "images/base-ubuntu-server.qcow2"
    if not os.path.exists(base_image):
        print(f"ОШИБКА: Базовый образ {base_image} не найден!")
        print("Пожалуйста, скопируйте ваш образ в папку images/")
        return
    
    try:
        port_manager = PortManager()
        qemu_manager = QEMUManager()
    except Exception as e:
        print(f"Ошибка инициализации: {e}")
        return
    
    vm_id = f"test-vm-{int(time.time())}"
    
    print(f"\n1. Получаем порт для ВМ {vm_id}")
    port = port_manager.get_next_port(vm_id)
    print(f"   -> Порт: {port}")
    
    print(f"\n2. Создаем ВМ")
    try:
        vm_info = qemu_manager.create_vm(
            os_type="ubuntu",
            cpu=1,
            ram=1024,
            port=port,
            vm_id=vm_id,
            user_id="test-user",
            timeout_minutes=2
        )
        print("   -> ВМ создана")
        
        port_manager.reserve_port(vm_id, port)
        
    except Exception as e:
        print(f"   -> Ошибка: {e}")
        return
    
    print(f"\n3. Список ВМ")
    time.sleep(3)
    vms = qemu_manager.list_vms()
    print(f"   -> Найдено ВМ: {len(vms)}")
    for vm in vms:
        print(f"      ID: {vm['id']}, Status: {vm['status']}")
    
    print(f"\n4. SSH команда:")
    print(f"   {qemu_manager.get_ssh_command(vm_id)}")
    
    print(f"\n5. Ждем 30 секунд...")
    for i in range(30):
        time.sleep(1)
        if i % 10 == 0:
            print(f"   прошло {i}с")
    
    print(f"\n6. Удаляем ВМ")
    qemu_manager.delete_vm(vm_id)
    port_manager.release_port(vm_id)
    
    print("\nГотово!")

if __name__ == "__main__":
    main()
