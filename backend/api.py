from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend import state_manager
from managers.docker_manager import DockerManager
from managers.qemu_manager import QemuManager
from backend.port_manager import get_next_port

app = FastAPI(title="Hosting Lab API")

docker_manager = DockerManager()
qemu_manager = QemuManager()

class CreateRequest(BaseModel):
    type: str
    cpu: int
    ram: int

@app.post("/create")
def create_instance(request: CreateRequest):
    """
    Создаёт новый ресурс (контейнер или VM)
    """
    port = get_next_port(request.type)

    state = state_manager.load_state()
    count = len([k for k in state if k.startswith(request.type + "_")])
    new_id = f"{request.type}_{count + 1}"

    if request.type == "docker":
        try:
            instance = docker_manager.create_container(
                request.cpu,
                request.ram,
                port,
                new_id
            )
            state_manager.add_object(new_id, instance)
            return {"message": "created", "id": new_id, "details": instance}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    elif request.type == "vm":
        try:
            instance = qemu_manager.create_vm(
                cpu=request.cpu,
                ram=request.ram,
                port=port,
                vm_id=new_id
            )
            return {"message": "created", "id": new_id, "details": instance}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail="Invalid type: must be 'docker' or 'vm'")

@app.get("/list")
def get_all_instances():
    """
    Возвращает список всех запущенных ресурсов
    """
    return state_manager.load_state()

@app.delete("/delete/{instance_id}")
def delete_instance(instance_id: str):
    """
    Удаляет ресурс по ID
    """
    state = state_manager.load_state()
    if instance_id not in state:
        raise HTTPException(status_code=404, detail="Resource not found")

    if instance_id.startswith("docker_"):
        try:
            docker_manager.delete_container(instance_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting Docker: {str(e)}")

    elif instance_id.startswith("vm_"):
        try:
            qemu_manager.delete_vm(instance_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting VM: {str(e)}")

    state_manager.delete_object(instance_id)

    return {"message": "deleted", "id": instance_id}
