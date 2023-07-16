from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query

from exceptions import ResourceNotFoundException, ResourceBlockException, ResourceReleaseException
from models.pydantic_models import ResourceOut, ResourcesOut, ResourceIn, Status
from resource_service import ResourceService

app = FastAPI(title="resource-usage-app")

resource_service: ResourceService = ResourceService()


@app.get("/healthcheck", status_code=200)
async def healthcheck():
    return "OK"


@app.get("/resources", status_code=200)
def get_resources(status: Optional[Status] = Query(None, description="Filter resources by status"),
                  tags: list[str] = Query(None)) -> ResourcesOut:
    return resource_service.get_resources(status, tags)


@app.post("/resources", status_code=200)
def create_resource(resource_in: ResourceIn) -> ResourceOut:
    return resource_service.create_resource(resource_in)


@app.delete("/resources/{resource_id}", status_code=200)
def remove_resource(resource_id: str):
    try:
        resource_service.remove_resource(resource_id)
        return {"message": f"Resource {resource_id} was removed"}
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/resources/{resource_id}", status_code=200)
def get_resource(resource_id: str) -> ResourceOut:
    try:
        return resource_service.get_resource(resource_id)
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/resources/{resource_id}/block", status_code=200)
def block_resource(resource_id: str):
    try:
        resource_service.block_resource(resource_id)
        return {"message": f"Resource {resource_id} was blocked"}
    except ResourceBlockException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/resources/{resource_id}/release", status_code=200)
def release_resource(resource_id: str):
    try:
        resource_service.release_resource(resource_id)
        return {"message": f"Resource {resource_id} was released"}
    except ResourceReleaseException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.on_event("shutdown")
def shutdown_event():
    resource_service.close_connection()


@app.on_event("startup")
def startup_event():
    # Create tables if they don't exist on application startup
    resource_service.init_db()
