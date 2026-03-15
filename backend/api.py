from fastapi import FastAPI, HTTPException
from managers.docker_manager import DockerManager
from backend.port_manager import PortManager
from backend.state_manager import StateManager

app = FastAPI(title="LW4 Docker Backend + Extra")

docker_manager = DockerManager()

@app.post("/docker/create")
def create_docker(os: str, cpu: int, ram: int):
    port = PortManager.get_next_docker_port()
    state = StateManager.load()
    next_num = len([k for k in state if k.startswith("docker_")]) + 1
    instance_id = f"docker_{next_num}"

    try:
        instance = docker_manager.create_container(os, cpu, ram, port, instance_id)
        return instance
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get("/docker/list")
def list_docker():
    return docker_manager.list_containers()

@app.post("/docker/delete/{instance_id}")
def delete_docker(instance_id: str):
    docker_manager.delete_container(instance_id)
    return {"success": True}
