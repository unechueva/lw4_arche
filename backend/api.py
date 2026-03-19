from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend import state_manager
from managers.docker_manager import DockerManager
from backend.port_manager import get_next_port

app = FastAPI(title="Hosting Lab API")

docker_manager = DockerManager()

class CreateRequest(BaseModel):
    type: str
    cpu: int
    ram: int

@app.post("/create")
def create_instance(request: CreateRequest):
    port = get_next_port(request.type)
    
    if request.type == "docker":
        try:
            instance = docker_manager.create_container(request.cpu, request.ram, port, f"docker_{len(state_manager.load_state()) + 1}")
            state_manager.add_object(instance["id"], instance)
            return {"message": "created", "id": instance["id"], "details": instance}
        except Exception as e:
            raise HTTPException(400, str(e))
    
    elif request.type == "vm":
        new_id = f"vm_{len(state_manager.load_state()) + 1}"
        data = {
            "type": "vm",
            "cpu": request.cpu,
            "ram": request.ram,
            "port": port,
            "status": "created (заглушка)"
        }
        state_manager.add_object(new_id, data)
        return {"message": "created", "id": new_id, "details": data}
    
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
    
    state_manager.delete_object(instance_id)
    return {"message": "deleted", "id": instance_id}
