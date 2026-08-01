import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Query, Request, Response, status
from fastapi.responses import JSONResponse

from src.exceptions import ResourceBlockException, ResourceNotFoundException, ResourceReleaseException
from src.models.enums import ResourceOperationType, Status
from src.models.filters import PaginationParams, ResourceFilter, ResourceHistoryFilter
from src.models.pydantic_models import (
    ClaimRequest,
    OperationRequest,
    ResourceIn,
    ResourceOut,
    ResourcesOperationsOut,
    ResourcesOut,
)
from src.resource_service import ResourceService, create_resource_service

app = FastAPI(title="resource-usage-app")

PaginationDep = Annotated[PaginationParams, Depends()]
ResourceServiceDep = Annotated[ResourceService, Depends(create_resource_service)]
StatusQuery = Annotated[Status | None, Query()]
TagsQuery = Annotated[list[str] | None, Query()]


@app.exception_handler(ResourceNotFoundException)
def handle_not_found(_request: Request, exc: ResourceNotFoundException) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(ResourceBlockException)
@app.exception_handler(ResourceReleaseException)
def handle_state_conflict(_request: Request, exc: ResourceBlockException | ResourceReleaseException) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.get("/healthcheck", status_code=200)
async def healthcheck():
    return "OK"


@app.get("/resources/actions")
def get_actions(
    resource_id: UUID | None = None,
    operation: ResourceOperationType | None = None,
    start_date: datetime.datetime | None = None,
    end_date: datetime.datetime | None = None,
    *,
    pagination: PaginationDep,
    resource_service: ResourceServiceDep,
) -> ResourcesOperationsOut:
    filters = ResourceHistoryFilter(
        resource_id=str(resource_id) if resource_id else None,
        operation=operation,
        start_date=start_date,
        end_date=end_date,
    )
    return resource_service.get_resources_history(filters, pagination)


@app.get("/resources", status_code=200)
def get_resources(
    status: StatusQuery = None,
    tags: TagsQuery = None,
    *,
    pagination: PaginationDep,
    resource_service: ResourceServiceDep,
) -> ResourcesOut:
    resource_filter = ResourceFilter(status=status, tags=tags or [])
    return resource_service.get_resources(resource_filter, pagination)


@app.post("/resources", status_code=status.HTTP_201_CREATED)
def create_resource(resource_in: ResourceIn, resource_service: ResourceServiceDep) -> ResourceOut:
    return resource_service.create_resource(resource_in)


@app.post(
    "/resources/claim",
    responses={204: {"description": "No matching resource available"}},
)
def claim_resource(
    claim_request: ClaimRequest,
    response: Response,
    resource_service: ResourceServiceDep,
) -> ResourceOut | None:
    resource = resource_service.claim_resource(claim_request)
    if resource is None:
        response.status_code = status.HTTP_204_NO_CONTENT
        return None
    return resource


@app.delete("/resources/{resource_id}", status_code=200)
def remove_resource(resource_id: UUID, resource_service: ResourceServiceDep):
    resource_service.remove_resource(str(resource_id))
    return {"message": f"Resource {resource_id} was removed"}


@app.get("/resources/{resource_id}", status_code=200)
def get_resource(resource_id: UUID, resource_service: ResourceServiceDep) -> ResourceOut:
    return resource_service.get_resource(str(resource_id))


@app.put("/resources/{resource_id}/block", status_code=200)
def block_resource(
    resource_id: UUID,
    block_request: OperationRequest,
    resource_service: ResourceServiceDep,
):
    resource_service.block_resource(resource_id, block_request)
    return {"message": f"Resource {resource_id} was blocked"}


@app.put("/resources/{resource_id}/release", status_code=200)
def release_resource(resource_id: UUID, resource_service: ResourceServiceDep):
    resource_service.release_resource(resource_id)
    return {"message": f"Resource {resource_id} was released"}
