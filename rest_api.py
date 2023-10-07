import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, Depends

from exceptions import ResourceNotFoundException, ResourceBlockException, ResourceReleaseException
from models.enums import Status, ResourceOperationType
from models.filters import ResourceFilter, ResourceHistoryFilter, PaginationParams
from models.pydantic_models import ResourceOut, ResourcesOut, ResourceIn, ResourcesOperationsOut, OperationRequest
from resource_service import ResourceService, create_resource_service

app = FastAPI(title="resource-usage-app")


@app.get("/healthcheck", status_code=200)
async def healthcheck():
    return "OK"


@app.get("/resources/actions", response_model=ResourcesOperationsOut)
def get_actions(resource_id: Optional[str] = None,
                operation: Optional[ResourceOperationType] = None,
                start_date: Optional[datetime.datetime] = None,
                end_date: Optional[datetime.datetime] = None,
                pagination: PaginationParams = Depends(),
                resource_service: ResourceService = Depends(create_resource_service)):
    filters = ResourceHistoryFilter(
        resource_id=resource_id,
        operation=operation,
        start_date=start_date,
        end_date=end_date
    )
    return resource_service.get_resources_history(filters, pagination)


@app.get("/resources", status_code=200, response_model=ResourcesOut)
def get_resources(status: Optional[Status] = Query(None),
                  tags: Optional[List[str]] = Query(None, description="Comma-separated list of tags"),
                  pagination: PaginationParams = Depends(),
                  resource_service: ResourceService = Depends(create_resource_service)
                  ) -> ResourcesOut:
    if tags:
        tags = [tag.strip() for tag in tags[0].split(',')]
    resource_filter = ResourceFilter(status=status, tags=tags)
    return resource_service.get_resources(resource_filter, pagination)


@app.post("/resources", status_code=200, response_model=ResourceOut)
def create_resource(resource_in: ResourceIn,
                    resource_service: ResourceService = Depends(create_resource_service)) -> ResourceOut:
    return resource_service.create_resource(resource_in)


@app.delete("/resources/{resource_id}", status_code=200)
def remove_resource(resource_id: str, resource_service: ResourceService = Depends(create_resource_service)):
    try:
        resource_service.remove_resource(resource_id)
        return {"message": f"Resource {resource_id} was removed"}
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/resources/{resource_id}", status_code=200, response_model=ResourceOut)
def get_resource(resource_id: str, resource_service: ResourceService = Depends(create_resource_service)) -> ResourceOut:
    try:
        return resource_service.get_resource(resource_id)
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/resources/{resource_id}/block", status_code=200)
def block_resource(resource_id: str, block_request: OperationRequest,
                   resource_service: ResourceService = Depends(create_resource_service)):
    try:
        resource_service.block_resource(resource_id, block_request)
        return {"message": f"Resource {resource_id} was blocked"}
    except ResourceBlockException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/resources/{resource_id}/release", status_code=200)
def release_resource(resource_id: str, resource_service: ResourceService = Depends(create_resource_service)):
    try:
        resource_service.release_resource(resource_id)
        return {"message": f"Resource {resource_id} was released"}
    except ResourceReleaseException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.on_event("shutdown")
def shutdown_event():
    pass
    # resource_service.close_connection()


@app.on_event("startup")
def startup_event():
    pass
    # Create tables if they don't exist on application startup
    # resource_repository.init_db()
