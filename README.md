## Формат состояния

Состояние хранится в app/data/state.json.

Пример:
{
  "vm_1": {
    "type": "vm",
    "cpu": 1,
    "ram": 512,
    "port": 2300,
    "status": "running"
  }
}

## Диапазоны портов

Docker:
начальный порт 2222

QEMU VM:
начальный порт 2300

Порт определяется как max(existing) + 1.
Если объектов нет, используется стартовый порт.

## Тестирование

1. Запустить backend:  
   `uvicorn backend.api:app --reload`

2. Запустить frontend:  
   `streamlit run frontend/app.py`

3. В браузере: http://localhost:8501  
   Создавайте ресурсы типа "docker", подключайтесь по SSH (root/toor)

Логин/пароль в контейнерах: root / toor
Порты Docker: 2222 и выше
