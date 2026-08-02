import asyncio
import datetime
import logging
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Query, Request, Response, status
from fastapi.responses import JSONResponse

from src.config.default import get_settings
from src.exceptions import (
    ResourceBlockException,
    ResourceLeaseValidationException,
    ResourceNotFoundException,
    ResourceReleaseException,
    ResourceRenewException,
)
from src.models.enums import ResourceOperationType, Status
from src.models.filters import PaginationParams, ResourceFilter, ResourceHistoryFilter
from src.models.pydantic_models import (
    ClaimRequest,
    LeaseRequest,
    ReleaseRequest,
    RenewRequest,
    ResourceIn,
    ResourceLeaseOut,
    ResourceOut,
    ResourcesOperationsOut,
    ResourcesOut,
)
from src.resource_service import ResourceService, create_resource_service

logger = logging.getLogger(__name__)


async def lease_cleanup_loop() -> None:
    settings = get_settings()
    interval_seconds = settings.app_lease_cleanup_interval_minutes * 60

    while True:
        await asyncio.sleep(interval_seconds)
        try:
            released_count = create_resource_service().release_expired_leases()
            if released_count:
                logger.info("Released %s expired resource leases", released_count)
        except Exception:
            logger.exception("Failed to release expired resource leases")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    cleanup_task = None
    if get_settings().app_lease_cleanup_enabled:
        cleanup_task = asyncio.create_task(lease_cleanup_loop())
    try:
        yield
    finally:
        if cleanup_task:
            cleanup_task.cancel()


app = FastAPI(title="resource-coordinator", lifespan=lifespan)

PaginationDep = Annotated[PaginationParams, Depends()]
ResourceServiceDep = Annotated[ResourceService, Depends(create_resource_service)]
StatusQuery = Annotated[Status | None, Query()]
TagsQuery = Annotated[list[str] | None, Query()]


@app.exception_handler(ResourceNotFoundException)
def handle_not_found(_request: Request, exc: ResourceNotFoundException) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(ResourceBlockException)
@app.exception_handler(ResourceReleaseException)
@app.exception_handler(ResourceRenewException)
def handle_state_conflict(
    _request: Request, exc: ResourceBlockException | ResourceReleaseException | ResourceRenewException
) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.exception_handler(ResourceLeaseValidationException)
def handle_lease_validation(_request: Request, exc: ResourceLeaseValidationException) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


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
) -> ResourceLeaseOut | None:
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
    block_request: LeaseRequest,
    resource_service: ResourceServiceDep,
) -> ResourceLeaseOut:
    return resource_service.block_resource(resource_id, block_request)


@app.put("/resources/{resource_id}/release", status_code=200)
def release_resource(
    resource_id: UUID,
    release_request: ReleaseRequest,
    resource_service: ResourceServiceDep,
):
    resource_service.release_resource(resource_id, release_request)
    return {"message": f"Resource {resource_id} was released"}


@app.put("/resources/{resource_id}/renew", status_code=200)
def renew_resource(
    resource_id: UUID,
    renew_request: RenewRequest,
    resource_service: ResourceServiceDep,
) -> ResourceLeaseOut:
    return resource_service.renew_resource(resource_id, renew_request)
