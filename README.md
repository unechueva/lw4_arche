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

## Как запустить проект

1. `source venv/bin/activate`
2. `uvicorn backend.api:app --reload`  ← backend
3. В новом терминале: `streamlit run frontend/app.py`

Порты:
- Docker: 2222+
- VM: 2300+

Логин/пароль в контейнерах: root / toor
