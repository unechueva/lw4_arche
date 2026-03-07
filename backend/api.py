from fastapi import FastAPI
from pydantic import BaseModel
from backend import state_manager

app = FastAPI(title="Hosting Lab API")

class CreateRequest(BaseModel):
    type: str
    cpu: int
    ram: int

@app.post("/create")
def create_instance(request: CreateRequest):
    state = state_manager.load_state()
    count = len([k for k in state if k.startswith(request.type + "_")])
    new_id = f"{request.type}_{count + 1}"

    port_start = 2300 if request.type == "vm" else 2222
    data = {
        "type": request.type,
        "cpu": request.cpu,
        "ram": request.ram,
        "port": port_start + count,
        "status": "created (заглушка)"
    }

    state_manager.add_object(new_id, data)
    return {"message": "created", "id": new_id, "details": data}

@app.get("/list")
def get_all_instances():
    return state_manager.load_state()

@app.delete("/delete/{instance_id}")
def delete_instance(instance_id: str):
    state_manager.delete_object(instance_id)
    return {"message": "deleted", "id": instance_id}
