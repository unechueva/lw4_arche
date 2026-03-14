л# Интерфейсы менеджеров

## DockerManager

Методы:
create_container(cpu, ram, port, id)
delete_container(id)
list_containers()

## QemuManager

Методы:
create_vm(cpu, ram, port, id)
delete_vm(id)
list_vm()

## Формат возвращаемого объекта

Каждый метод create должен возвращать словарь строго такого формата:

{
  "id": "...",
  "type": "...",
  "cpu": ...,
  "ram": ...,
  "port": ...,
  "status": "running"
}
