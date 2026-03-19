from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend import state_manager
from managers.docker_manager import DockerManager
from managers.qemu_manager import QemuManager
from backend.port_manager import PortManager

app = FastAPI(title="Hosting Lab API")

docker_manager = DockerManager()
qemu_manager = QemuManager()

class CreateRequest(BaseModel):
    type: str  # "docker" | "vm"
    cpu: int
    ram: int

@app.post("/create")
def create_instance(request: CreateRequest):
    state = state_manager.load_state()
    count = len([k for k in state if k.startswith(request.type + "_")])
    new_id = f"{request.type}_{count + 1}"

    port = PortManager.get_next_port(request.type)

    if request.type == "docker":
        try:
            instance = docker_manager.create_container(request.cpu, request.ram, port, new_id)
            state_manager.add_object(new_id, instance)
            return {"message": "created", "id": new_id, "details": instance}
        except Exception as e:
            raise HTTPException(400, str(e))
    
    elif request.type == "vm":
        data = {
            "type": "vm",
            "cpu": request.cpu,
            "ram": request.ram,
            "port": port,
            "status": "created (заглушка VM)"
        }
        state_manager.add_object(new_id, data)
        return {"message": "created", "id": new_id, "details": data}
    
    else:
        raise HTTPException(400, "Invalid type")

@app.get("/list")
def get_all_instances():
    return state_manager.load_state()

@app.delete("/delete/{instance_id}")
def delete_instance(instance_id: str):
    state = state_manager.load_state()
    if instance_id not in state:
        raise HTTPException(404, "Not found")
    
    if instance_id.startswith("docker_"):
        docker_manager.delete_container(instance_id)
    
    # elif instance_id.startswith("vm_"):
    #     qemu_manager.delete_vm(instance_id)
    
    state_manager.delete_object(instance_id)
    return {"message": "deleted", "id": instance_id}